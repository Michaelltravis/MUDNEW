// Misthollow platformer: DOM overlays.
// Room prose banner, HUD bars, hotbar, raw-MUD terminal drawer, chat overlay,
// inventory/journal/shop/spell modals. Everything is driven by map payloads
// plus parser events; every action funnels back through real MUD commands.
(() => {
  const MH = window.MH = window.MH || {};
  const NAME_KEY = 'misthollow_name';
  const PW_KEY = 'misthollow_pw';
  const HOTBAR_KEY = 'misthollow_plat_hotbar_v3';
  const BAR_SIZE = 10;
  const DEFAULT_HOTBAR = ['attack', 'flee', '', '', '', '', '', 'inventory', 'score', 'quests'];

  const $ = id => document.getElementById(id);
  const els = {};

  function lsGet(k) { try { return localStorage.getItem(k); } catch (_) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (_) {} }

  // ---- WebAudio cues: you should HEAR combat ----
  let audioCtx = null;
  function audio() {
    if (audioCtx) { if (audioCtx.state === 'suspended') audioCtx.resume().catch(() => {}); return audioCtx; }
    const Ref = window.AudioContext || window.webkitAudioContext;
    if (!Ref) return null;
    try { audioCtx = new Ref(); } catch (_) { return null; }
    return audioCtx;
  }
  function tone({ f = 440, f2 = null, type = 'square', dur = 0.12, vol = 0.08, delay = 0 }) {
    const ctx = audio();
    if (!ctx) return;
    const o = ctx.createOscillator(), g = ctx.createGain();
    const t = ctx.currentTime + delay;
    o.type = type;
    o.frequency.setValueAtTime(f, t);
    if (f2) o.frequency.linearRampToValueAtTime(f2, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + 0.015);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(ctx.destination);
    o.start(t); o.stop(t + dur + 0.02);
  }
  // white-noise burst layered under tones = physical crunch
  let noiseBuf = null;
  function noise({ dur = 0.07, vol = 0.1, delay = 0, low = false }) {
    const ctx = audio();
    if (!ctx) return;
    if (!noiseBuf) {
      noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 0.2, ctx.sampleRate);
      const data = noiseBuf.getChannelData(0);
      for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    }
    const srcN = ctx.createBufferSource();
    srcN.buffer = noiseBuf;
    const g = ctx.createGain();
    const t = ctx.currentTime + delay;
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    let node = srcN;
    if (low) {
      const f = ctx.createBiquadFilter();
      f.type = 'lowpass'; f.frequency.value = 700;
      srcN.connect(f); node = f;
    }
    node.connect(g); g.connect(ctx.destination);
    srcN.start(t); srcN.stop(t + dur + 0.02);
  }
  const sfx = {
    hit: () => { tone({ f: 320, f2: 240, type: 'square', dur: 0.08, vol: 0.05 }); noise({ dur: 0.05, vol: 0.07 }); },
    taken: () => { tone({ f: 130, f2: 70, type: 'sawtooth', dur: 0.2, vol: 0.12 }); noise({ dur: 0.1, vol: 0.14, low: true }); },
    death: () => [200, 150, 110, 80].forEach((f, i) => tone({ f, type: 'sawtooth', dur: 0.3, vol: 0.12, delay: i * 0.2 })),
    level: () => [261, 329, 392, 523].forEach((f, i) => tone({ f, type: 'triangle', dur: 0.14, vol: 0.09, delay: i * 0.13 })),
    move: () => tone({ f: 220, f2: 180, type: 'sine', dur: 0.08, vol: 0.04 }),
    engage: () => { tone({ f: 90, f2: 60, type: 'sawtooth', dur: 0.25, vol: 0.12 }); tone({ f: 520, dur: 0.1, vol: 0.05, delay: 0.05 }); },
  };

  // ---- output capture for shop/journal panels ----
  let capture = null;
  function captureOutput(ms) {
    return new Promise(resolve => {
      const mine = { lines: [], done: false };
      const finish = () => {
        if (mine.done) return;
        mine.done = true;
        if (capture === mine) capture = null;   // overlapping captures must not null each other
        resolve(mine.lines);
      };
      // snappy: resolve 250ms after the output stream goes quiet
      mine.bump = () => { clearTimeout(mine.idle); mine.idle = setTimeout(finish, 250); };
      capture = mine;
      setTimeout(finish, ms);                   // hard ceiling
    });
  }

  // ---- terminal drawer ----
  function appendTerminal(html, cls) {
    const div = document.createElement('div');
    if (cls) div.className = cls;
    if (cls) div.textContent = html;
    else div.innerHTML = html;
    els.drawerLog.appendChild(div);
    while (els.drawerLog.children.length > 600) els.drawerLog.removeChild(els.drawerLog.firstChild);
    els.drawerLog.scrollTop = els.drawerLog.scrollHeight;
  }

  // ---- hotbar 2.0: drawn icons, cooldown sweeps, drag-to-bind ----
  let hotbar = [];

  function iconKindFor(cmd) {
    const c = String(cmd || '').toLowerCase();
    if (!c) return 'empty';
    if (/^cast /.test(c)) return 'sparkle';
    if (/^(kill|attack|bash|kick|backstab|cleave|charge|strike|execute)/.test(c)) return 'sword';
    if (/^(look|examine|exits)/.test(c)) return 'eye';
    if (/^(flee|escape|disengage|retreat)/.test(c)) return 'boot';
    if (/^(rest|sleep|sit)/.test(c)) return 'zzz';
    if (/^(stand|wake)/.test(c)) return 'arrow';
    if (/^(inventory|equipment|wear|wield|get|drop)/.test(c)) return 'bag';
    if (/^(score|affects|skills|talents)/.test(c)) return 'chart';
    if (/^(quest|journal)/.test(c)) return 'scroll';
    if (/^(north|south|east|west|up|down|recall)/.test(c)) return 'compass';
    const p = MH.state.player;
    if (p && (p.class_skills || []).some(s => c.startsWith(s))) return 'star';
    return 'gear';
  }

  function drawIcon(canvas, kind) {
    const x = canvas.getContext('2d');
    x.clearRect(0, 0, 20, 20);
    const px = (c, ...rects) => { x.fillStyle = c; rects.forEach(r => x.fillRect(...r)); };
    switch (kind) {
      case 'sword': px('#c8ccd8', [9, 2, 2, 11]); px('#e8c168', [6, 12, 8, 2]); px('#8a6a3a', [9, 14, 2, 4]); break;
      case 'sparkle': px('#9ad6ff', [9, 3, 2, 14], [3, 9, 14, 2]); px('#ffffff', [8, 8, 4, 4]); break;
      case 'eye': px('#c8ccd8', [4, 8, 12, 4]); px('#2a6a9a', [8, 7, 4, 6]); px('#0a0c10', [9, 9, 2, 2]); break;
      case 'boot': px('#8a6a40', [7, 3, 4, 9]); px('#6a4e2c', [7, 12, 8, 4]); break;
      case 'zzz': px('#9aa0b4', [4, 4, 6, 2], [6, 7, 4, 2], [4, 10, 6, 2], [10, 12, 5, 2], [12, 15, 3, 2]); break;
      case 'arrow': px('#7ad68a', [9, 3, 2, 12], [6, 6, 2, 2], [12, 6, 2, 2], [4, 8, 2, 2], [14, 8, 2, 2]); break;
      case 'bag': px('#8a6a40', [5, 7, 10, 9]); px('#6a4e2c', [7, 4, 6, 4]); px('#e8c168', [9, 10, 2, 2]); break;
      case 'chart': px('#5c6478', [3, 15, 14, 2]); px('#7ad68a', [4, 10, 3, 5]); px('#e8c168', [9, 6, 3, 9]); px('#e06c6c', [14, 12, 3, 3]); break;
      case 'scroll': px('#e0d8c0', [5, 3, 10, 14]); px('#8a7a5a', [7, 6, 6, 1], [7, 9, 6, 1], [7, 12, 4, 1]); break;
      case 'compass': px('#c8ccd8', [9, 2, 2, 16], [2, 9, 16, 2]); px('#e06c6c', [9, 4, 2, 5]); break;
      case 'star': px('#ffd44a', [9, 3, 2, 14], [4, 8, 12, 2], [6, 5, 2, 2], [12, 5, 2, 2], [6, 13, 2, 2], [12, 13, 2, 2]); break;
      case 'gear': px('#9aa0b4', [7, 7, 6, 6], [9, 3, 2, 4], [9, 13, 2, 4], [3, 9, 4, 2], [13, 9, 4, 2]); break;
      default: px('#2a2f3c', [8, 9, 4, 2]); break;
    }
  }

  function loadHotbar() {
    try { hotbar = JSON.parse(lsGet(HOTBAR_KEY)) || DEFAULT_HOTBAR.slice(); }
    catch (_) { hotbar = DEFAULT_HOTBAR.slice(); }
    if (!Array.isArray(hotbar) || hotbar.length !== BAR_SIZE) hotbar = DEFAULT_HOTBAR.slice();
    renderHotbar();
  }

  // WoW-style quality of life: first time a class logs in, fill the empty
  // slots with their actual spells and skills
  let autofilled = false;
  function autofillBar() {
    const pdata = MH.state.player;
    if (autofilled || !pdata || !pdata.char_class) return;
    autofilled = true;
    const fillKey = `misthollow_bar_filled_${(pdata.name || '').toLowerCase()}`;
    if (lsGet(fillKey)) return;
    // internal ability ids use underscores; the cast parser wants spaces
    const abilities = (pdata.class_spells || []).map(s => `cast '${s.replace(/_/g, ' ')}'`)
      .concat((pdata.class_skills || []).map(s => s.replace(/_/g, ' ')));
    let changed = false;
    for (let i = 0; i < BAR_SIZE && abilities.length; i++) {
      if (!hotbar[i]) { hotbar[i] = abilities.shift(); changed = true; }
    }
    if (changed) {
      lsSet(HOTBAR_KEY, JSON.stringify(hotbar));
      lsSet(fillKey, '1');
      renderHotbar();
      flash('Your abilities are on the action bar - drag from K to customize.');
    }
  }

  function bindSlot(i, cmd) {
    hotbar[i] = String(cmd || '').trim();
    lsSet(HOTBAR_KEY, JSON.stringify(hotbar));
    renderHotbar();
  }

  function renderHotbar() {
    els.hotbar.innerHTML = '';
    const skills = (MH.state.player && MH.state.player.skills) || {};
    hotbar.forEach((cmd, i) => {
      const slot = document.createElement('div');
      slot.className = 'hotslot';
      const skillName = String(cmd || '').replace(/^cast '/, '').replace(/'$/, '');
      const prof = skills[skillName];
      slot.setAttribute('draggable', 'true');
      slot.innerHTML = `<span class="key">${(i + 1) % 10}</span>`
        + (prof != null ? `<span class="prof">${prof}%</span>` : '')
        + `<canvas width="20" height="20"></canvas>`
        + `<span class="lbl">${cmd || '—'}</span><div class="cd"></div>`;
      drawIcon(slot.querySelector('canvas'), iconKindFor(cmd));
      slot.title = `${cmd || 'empty'}\n(right-click to rebind, drag a skill here from K)`;
      slot.addEventListener('click', () => useHotbar(i));
      slot.addEventListener('contextmenu', e => {
        e.preventDefault();
        const next = prompt(`Command for slot ${i + 1}:`, hotbar[i] || '');
        if (next !== null) bindSlot(i, next);
      });
      slot.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', `slot:${i}`));
      slot.addEventListener('dragover', e => { e.preventDefault(); slot.classList.add('dragover'); });
      slot.addEventListener('dragleave', () => slot.classList.remove('dragover'));
      slot.addEventListener('drop', e => {
        e.preventDefault();
        slot.classList.remove('dragover');
        const data = e.dataTransfer.getData('text/plain');
        if (!data) return;
        const m = data.match(/^slot:(\d+)$/);
        if (m) {
          // reorder: swap the two slots
          const j = Number(m[1]);
          if (j !== i) { const tmp = hotbar[i]; bindSlot(i, hotbar[j]); bindSlot(j, tmp); }
        } else {
          bindSlot(i, data);
        }
      });
      els.hotbar.appendChild(slot);
    });
  }

  // raw commands print to the hidden terminal, which reads as "nothing
  // happened" - so peek the response into the flash banner
  async function commandWithPeek(cmd) {
    const p = captureOutput(1100);
    MH.sendCommand(cmd);
    const lines = await p;
    const first = lines.find(l => l.trim() && !/^\d+\/\d+hp/i.test(l) && !/^>/.test(l));
    if (first) flash(first.slice(0, 90));
  }

  function useHotbar(i) {
    const cmd = hotbar[i];
    if (!cmd) return;
    // slots map to real UI where possible - commands shouldn't vanish into
    // the void
    if (cmd === 'attack' || cmd === 'kill') {
      const t = currentTarget ? MH.mobKeyword(currentTarget.name) : '';
      if (cmd === 'kill' && t) MH.sendCommand(`kill ${t}`);
      else MH.bus.emit('player.attack');
    } else if (cmd === 'inventory' || cmd === 'equipment') {
      renderInventory(); openModal('modal-inv');
    } else if (cmd === 'quests' || cmd === 'journal') {
      openJournal();
    } else if (cmd === 'score') {
      openTextPanel('score');
    } else if (cmd === 'look') {
      if (lastRoomShown) showRoom(lastRoomShown.room, lastRoomShown.zoneName);
      commandWithPeek('look');
    } else if (/^cast '[^']+'$/.test(cmd)) {
      const spell = (cmd.match(/^cast '([^']+)'$/) || [])[1] || '';
      const ally = MH.state.allyTarget;
      if (ally && ally.until > Date.now() && /cure|heal|bless|armor|shield|sanctuary|renew|mend|protection|haste|barkskin|aegis|prayer|serenity|hymn|spirit_link|hand_of_freedom/i.test(spell)) {
        MH.sendCommand(`${cmd} ${ally.name}`);
      } else if (currentTarget) {
        MH.sendCommand(`${cmd} ${MH.mobKeyword(currentTarget.name)}`);
      } else {
        commandWithPeek(cmd);
      }
    } else {
      commandWithPeek(cmd);
    }
    // cooldown sweep ~ one combat round
    const slot = els.hotbar.children[i];
    if (slot) {
      const cd = slot.querySelector('.cd');
      cd.classList.remove('run');
      void cd.offsetWidth; // restart the animation
      cd.classList.add('run');
    }
  }

  // ---- HUD ----
  function setBar(barEl, txtEl, val, max) {
    const frac = max > 0 ? Math.max(0, Math.min(1, val / max)) : 0;
    barEl.style.width = `${frac * 100}%`;
    txtEl.textContent = `${val} / ${max}`;
  }
  function updateHud(player) {
    if (!player) return;
    els.hudName.textContent = `${player.name}${player.title ? ' ' + player.title : ''}`;
    setBar(els.barHp, els.txtHp, player.hp || 0, player.max_hp || 1);
    setBar(els.barMana, els.txtMana, player.mana || 0, player.max_mana || 1);
    setBar(els.barMove, els.txtMove, player.move || 0, player.max_move || 1);
    els.hudLevel.textContent = `Lv ${player.level} ${player.char_class || ''}`;
    els.hudGold.textContent = `${player.gold || 0} gold`;
    // xp progress within the current level (exp is cumulative)
    const floor = player.exp_floor || 0, next = player.exp_to_level || 0;
    if (next > floor) {
      const frac = Math.max(0, Math.min(1, ((player.exp || 0) - floor) / (next - floor)));
      els.barXp.style.width = `${frac * 100}%`;
      els.hudXpTxt.textContent = `${Math.floor(frac * 100)}% xp`;
    } else {
      els.barXp.style.width = '100%';
      els.hudXpTxt.textContent = '';
    }
    drawHudPortrait(player);
  }

  // headshot with shoulders in the dock, plus your wielded weapon's icon
  let portraitKey = null;
  function drawHudPortrait(p) {
    const c = document.getElementById('hud-portrait');
    if (!c || !window.MH || !MH.game) return;
    const wield = (p.equipment && p.equipment.wield && p.equipment.wield.name) || '';
    const key = `${p.char_class}|${p.aura || ''}|${wield}`;
    if (key === portraitKey) return;
    portraitKey = key;
    const ctx = c.getContext('2d');
    ctx.clearRect(0, 0, c.width, c.height);
    try {
      const scene = MH.game.scene.getScenes(true)[0];
      const texKey = MH.tdSprites.playerKey((p.char_class || '').toLowerCase());
      const tex = scene.textures.get(scene.textures.exists(texKey) ? texKey : 'td_player_warrior');
      const f = tex.get('d0');
      if (p.aura) {
        const sig = { warrior: '#e05a4a', paladin: '#ffe9a8', mage: '#9a8aff', necromancer: '#9adba0',
          thief: '#b8b2c8', assassin: '#8a5a9a', ranger: '#8ac06a', cleric: '#cfe2ff', bard: '#f0b060' }[(p.char_class || '').toLowerCase()] || '#e8c168';
        const g = ctx.createRadialGradient(c.width / 2, c.height * 0.45, 4, c.width / 2, c.height * 0.45, c.width * 0.7);
        g.addColorStop(0, sig + '66'); g.addColorStop(1, sig + '00');
        ctx.fillStyle = g; ctx.fillRect(0, 0, c.width, c.height);
      }
      ctx.imageSmoothingEnabled = false;
      // head & shoulders: the upper ~2/3 of the frame, blown up
      ctx.drawImage(tex.getSourceImage(), f.cutX, f.cutY + f.cutHeight * 0.06, f.cutWidth, f.cutHeight * 0.66,
        -10, 4, c.width + 20, c.height + 8);
    } catch (_) { /* decorative */ }
    const w = document.getElementById('hud-weapon');
    if (w) {
      const wctx = w.getContext('2d');
      wctx.clearRect(0, 0, w.width, w.height);
      if (p.equipment && p.equipment.wield && MH.itemIcons) MH.itemIcons.intoCanvas(w, p.equipment.wield);
    }
  }

  // ---- target frame ----
  let currentTarget = null;
  function setTarget(data) {
    const prev = currentTarget;
    currentTarget = data;
    if (!data) { els.targetFrame.classList.remove('show'); return; }
    els.targetFrame.classList.add('show');
    els.targetName.textContent = `${data.name} (Lv ${data.level || '?'})`;
    const max = data.maxHp || 1, hp = data.hp != null ? data.hp : max;
    const pct = Math.max(0, Math.min(100, (hp / max) * 100));
    // ghost layer snaps to the OLD value then drains slowly behind the real bar
    if (!prev || prev.name !== data.name) els.targetHpGhost.style.width = `${pct}%`;
    els.targetHp.style.width = `${pct}%`;
    requestAnimationFrame(() => { els.targetHpGhost.style.width = `${pct}%`; });
    els.targetHpTxt.textContent = `${hp} / ${max}`;
  }

  // ---- room banner / description ----
  // first visit: prose fades in over the scene; revisits show just the
  // name. L re-reads the room anytime (the MUD 'look' reflex).
  let descTimer = null;
  let lastRoomShown = null;
  let seenRooms = new Set();
  try { seenRooms = new Set(JSON.parse(localStorage.getItem('misthollow_seen_rooms') || '[]')); } catch (_) {}
  function rememberSeen(vnum) {
    if (seenRooms.has(vnum)) return;
    seenRooms.add(vnum);
    if (seenRooms.size > 4000) seenRooms = new Set([...seenRooms].slice(-3000));
    try { localStorage.setItem('misthollow_seen_rooms', JSON.stringify([...seenRooms])); } catch (_) {}
  }
  function showProse(room, holdMs) {
    const desc = (room.description || '').trim();
    if (!desc) { els.roomDesc.classList.remove('show'); return; }
    if (MH.immersion && MH.immersion.decorateProse) MH.immersion.decorateProse(els.roomDesc, desc, room);
    else els.roomDesc.textContent = desc;
    els.roomDesc.classList.add('show');
    clearTimeout(descTimer);
    descTimer = setTimeout(() => els.roomDesc.classList.remove('show'), holdMs);
  }
  function showRoom(room, zoneName) {
    lastRoomShown = { room, zoneName };
    els.roomName.textContent = room.name || '';
    els.roomZone.textContent = zoneName || '';
    const first = room.vnum != null && !seenRooms.has(room.vnum);
    if (room.vnum != null) rememberSeen(room.vnum);
    if (first) showProse(room, 7000);
    else els.roomDesc.classList.remove('show');
  }
  window.addEventListener('keydown', e => {
    if (e.key.toLowerCase() === 'l' && !e.ctrlKey && !e.metaKey
        && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)
        && lastRoomShown) {
      showProse(lastRoomShown.room, 9000);
    }
  });

  // ---- flash line ----
  let flashTimer = null;
  function flash(text) {
    els.flashLine.textContent = text;
    els.flashLine.classList.add('show');
    clearTimeout(flashTimer);
    flashTimer = setTimeout(() => els.flashLine.classList.remove('show'), 2200);
  }

  // dramatic center-top banner for world events
  let evtBannerTimer = null, lastEvt = 0;
  function eventAlert(title, sub, kind) {
    const el = document.getElementById('event-banner');
    if (!el) return;
    el.className = kind || '';
    el.innerHTML = `<div class="eb-t">${title}</div>${sub ? `<div class="eb-s">${sub}</div>` : ''}`;
    el.classList.add('show');
    clearTimeout(evtBannerTimer);
    evtBannerTimer = setTimeout(() => el.classList.remove('show'), 7000);
  }
  const EVENTS = [
    [/A WORLD BOSS HAS APPEARED|WORLD BOSS/i, () => ['👑 WORLD BOSS', 'A mighty foe has manifested — gather allies!', 'boss', 180]],
    [/INVASION!|forces of darkness march|undead are rising/i, () => ['⚔️ INVASION', 'Defenders needed — slay the invaders for glory!', '', 220]],
    [/Wave (\d+)\/(\d+)/i, (m) => [`⚔️ Invasion — Wave ${m[1]}/${m[2]}`, 'Hold the line!', '', 100]],
    [/TREASURE HUNT|treasure has been hidden|seek the/i, () => ['🗺 TREASURE HUNT', 'A prize awaits the first to solve the clue!', 'good', 260]],
    [/DOUBLE XP|double experience/i, () => ['✦ DOUBLE XP', 'Bonus experience is active — go hunt!', 'good', 330]],
  ];
  function detectWorldEvent(text) {
    if (!text || Date.now() - lastEvt < 1200) return;
    const clean = text.replace(/\x1b\[[0-9;]*m/g, '');
    for (const [re, fn] of EVENTS) {
      const m = clean.match(re);
      if (m) {
        lastEvt = Date.now();
        const [t, s, kind, freq] = fn(m);
        eventAlert(t, s, kind);
        try { tone({ f: freq || 200, f2: (freq || 200) * 1.5, type: 'sawtooth', dur: 0.3, vol: 0.06 }); } catch (_) {}
        return;
      }
    }
  }

  // rich corner toast for achievements / daily / title unlocks
  function toast(title, body, kind) {
    let host = document.getElementById('toast-host');
    if (!host) { host = document.createElement('div'); host.id = 'toast-host'; document.body.appendChild(host); }
    const t = document.createElement('div');
    t.className = 'mh-toast ' + (kind || '');
    t.innerHTML = `<div class="tt-t">${title}</div><div class="tt-b">${body}</div>`;
    host.appendChild(t);
    requestAnimationFrame(() => t.classList.add('in'));
    setTimeout(() => { t.classList.remove('in'); setTimeout(() => t.remove(), 400); }, 5200);
  }

  // ---- chat: tabbed panel + ambient overlay ----
  const chatStore = { all: [], party: [], say: [], channel: [], tell: [] };
  const unread = { party: 0, say: 0, channel: 0, tell: 0 };
  let activeTab = 'all';

  function classifyChat(line) {
    if (/tells? the group,|^You tell the group/i.test(line)) return 'party';
    if (/^(You tell|\w+ tells you)/i.test(line)) return 'tell';
    if (/^(You (gossip|shout|chat)|\w+ (gossips|shouts|chats))|^\[\w+\]/i.test(line)) return 'channel';
    if (/^(You say|\w+ says)/i.test(line)) return 'say';
    return 'say';
  }

  function renderChatBody() {
    const lines = chatStore[activeTab];
    els.chatBody.innerHTML = '';
    for (const { line, kind } of lines.slice(-120)) {
      const div = document.createElement('div');
      div.className = kind;
      div.textContent = line;
      els.chatBody.appendChild(div);
    }
    els.chatBody.scrollTop = els.chatBody.scrollHeight;
  }

  function updateBadges() {
    document.querySelectorAll('.chat-tab').forEach(tab => {
      const name = tab.dataset.tab;
      const badge = tab.querySelector('.badge');
      if (!badge || name === 'all') return;
      badge.textContent = unread[name] > 9 ? '9+' : String(unread[name] || '');
      badge.classList.toggle('show', unread[name] > 0);
    });
  }

  function chatPanelOpen() { return els.chatPanel.classList.contains('open'); }
  function toggleChatPanel(open) {
    const on = open != null ? open : !chatPanelOpen();
    els.chatPanel.classList.toggle('open', on);
    els.chatLog.style.display = on ? 'none' : '';
    if (on) {
      unread[activeTab] = 0;
      renderChatBody();
      updateBadges();
      els.chatInput.focus();
    } else {
      setTyping(false);
    }
  }

  function chatLine(line) {
    const kind = classifyChat(line);
    const entry = { line, kind };
    chatStore.all.push(entry);
    chatStore[kind].push(entry);
    for (const k of Object.keys(chatStore)) if (chatStore[k].length > 400) chatStore[k].shift();

    if (chatPanelOpen()) {
      if (activeTab === 'all' || activeTab === kind) renderChatBody();
      else { unread[kind]++; updateBadges(); }
    } else {
      if (unread[kind] !== undefined) { unread[kind]++; updateBadges(); }
      // ambient floating line
      const div = document.createElement('div');
      div.textContent = line;
      els.chatLog.appendChild(div);
      while (els.chatLog.children.length > 8) els.chatLog.removeChild(els.chatLog.firstChild);
      setTimeout(() => { if (div.parentNode) div.parentNode.removeChild(div); }, 12500);
    }
  }

  // ---- emote / social picker ----
  const EMOTES = [
    ['😊', 'smile'], ['👋', 'wave'], ['🙇', 'bow'], ['😂', 'laugh'], ['👍', 'nod'], ['🤗', 'hug'],
    ['😘', 'kiss'], ['👏', 'clap'], ['🎉', 'cheer'], ['😉', 'wink'], ['🤛', 'poke'], ['💃', 'dance'],
    ['🫡', 'salute'], ['💪', 'flex'], ['🙏', 'thank'], ['😢', 'cry'], ['😮', 'gasp'], ['🤦', 'facepalm'],
    ['🤷', 'shrug'], ['😏', 'snicker'], ['😴', 'yawn'], ['🙇', 'kneel'], ['😠', 'glare'], ['😈', 'cackle'],
  ];
  function emotePickerOpen(on) {
    const el = document.getElementById('emote-picker');
    if (!el) return;
    const show = on != null ? on : !el.classList.contains('show');
    if (!show) { el.classList.remove('show'); return; }
    const tgt = currentTarget ? currentTarget.name : (MH.state.allyTarget && MH.state.allyTarget.until > Date.now() ? MH.state.allyTarget.name : null);
    const kw = tgt ? MH.mobKeyword(tgt) : '';
    el.innerHTML = `<div class="ep-hd">EMOTES${tgt ? '' : ' · target someone to direct them'}</div>`
      + (tgt ? `<div class="ep-target">→ at ${tgt}</div>` : '')
      + '<div class="ep-grid">' + EMOTES.map(([ic, nm]) =>
          `<div class="ep" data-em="${nm}"><div class="ei">${ic}</div><div class="en">${nm}</div></div>`).join('') + '</div>';
    el.querySelectorAll('.ep').forEach(e => e.addEventListener('click', () => {
      MH.sendCommand(kw ? `${e.dataset.em} ${kw}` : e.dataset.em, false);
      emotePickerOpen(false);
    }));
    el.classList.add('show');
    const btn = document.getElementById('emote-btn');
    const r = btn.getBoundingClientRect();
    el.style.left = Math.min(r.left, window.innerWidth - 290) + 'px';
    el.style.top = (r.top - el.offsetHeight - 8) + 'px';
  }

  function sendChat() {
    const msg = els.chatInput.value.trim();
    if (!msg) return;
    const mode = els.chatMode.value;
    MH.sendCommand(mode === 'reply' ? `reply ${msg}` : `${mode} ${msg}`);
    els.chatInput.value = '';
  }

  // ---- modals ----
  // while any window is open the world is frozen to the mouse - no
  // drinking from fountains through the talent tree
  function setWorldInput(enabled) {
    MH.state.uiFrozen = !enabled;
    try {
      if (MH.game && MH.game.input) {
        MH.game.input.enabled = enabled;
        const sc = MH.game.scene.getScenes(true).find(s2 => s2.buildRoom);
        if (sc && sc.input.keyboard) sc.input.keyboard.enabled = enabled;
      }
    } catch (_) { /* game not booted yet */ }
    if (MH.popover && !enabled) MH.popover.hide();
  }
  MH.setWorldInput = setWorldInput;
  function openModal(id) {
    closeModals();
    $(id).classList.add('open');
    const bd = $('modal-backdrop');
    if (bd) bd.classList.add('show');
    setWorldInput(false);
  }
  function closeModals() {
    document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
    const bd = $('modal-backdrop');
    if (bd) bd.classList.remove('show');
    setWorldInput(true);
  }
  function anyModalOpen() { return !!document.querySelector('.modal.open'); }

  // paper-doll: your class character model wearing the gear, slot sockets
  // around it, carried items as an icon grid
  const PD_LEFT = ['head', 'neck', 'body', 'about', 'arms'];
  const PD_RIGHT = ['hands', 'waist', 'legs', 'feet', 'wrist'];
  const PD_BOTTOM = ['wield', 'shield', 'held', 'light', 'finger'];
  function drawCharModel(canvas, p) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // class aura behind the model when wearing legendaries / a full set
    if (p.aura && MH.itemIcons) {
      const cls = (p.char_class || 'warrior').toLowerCase();
      const sig = { warrior: '#e05a4a', paladin: '#ffe9a8', mage: '#9a8aff', necromancer: '#9adba0',
        thief: '#b8b2c8', assassin: '#8a5a9a', ranger: '#8ac06a', cleric: '#cfe2ff', bard: '#f0b060' }[cls] || '#e8c168';
      const g = ctx.createRadialGradient(canvas.width / 2, canvas.height * 0.55, 8, canvas.width / 2, canvas.height * 0.55, canvas.width * 0.48);
      g.addColorStop(0, sig + '55'); g.addColorStop(1, sig + '00');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    try {
      const scene = MH.game.scene.getScenes(true)[0];
      const texKey = MH.tdSprites.playerKey((p.char_class || '').toLowerCase());
      const tex = scene.textures.get(scene.textures.exists(texKey) ? texKey : 'td_player_warrior');
      const frame = tex.get('d0');
      ctx.imageSmoothingEnabled = false;
      const sz = Math.min(canvas.width, canvas.height) * 0.86;
      ctx.drawImage(tex.getSourceImage(), frame.cutX, frame.cutY, frame.cutWidth, frame.cutHeight,
        (canvas.width - sz) / 2, (canvas.height - sz) / 2, sz, sz);
    } catch (_) { /* model is decorative */ }
  }
  function pdSocket(slot, item) {
    const filled = item ? '' : ' empty';
    const rar = item ? (item.set_id ? 'set' : (item.rarity || 'common')) : '';
    return `<div class="pd-socket${filled}" data-slot="${slot}" ${item ? `data-name="${item.name}" data-cmd="remove ${MH.mobKeyword(item.name)}"` : ''} title="${item ? item.name + ' (click to remove)' : slot}">`
      + `<canvas width="34" height="34"></canvas><span class="pd-slotname">${slot}</span>${item && rar !== 'common' ? `<i class="pd-rar ${rar}"></i>` : ''}</div>`;
  }
  function renderInventory() {
    const p = MH.state.player;
    if (!p) { els.invBody.textContent = 'No data yet.'; return; }
    const eq = p.equipment || {};
    const known = new Set([...PD_LEFT, ...PD_RIGHT, ...PD_BOTTOM]);
    const extra = Object.keys(eq).filter(sl => !known.has(sl));
    let html = '<div class="pdoll">';
    html += '<div class="pd-col">' + PD_LEFT.map(sl => pdSocket(sl, eq[sl])).join('') + '</div>';
    html += `<div class="pd-center"><canvas id="pd-model" width="150" height="170"></canvas>`
      + `<div class="pd-class">${p.name || ''}<br><span>${p.char_class || ''}${p.aura ? ' · ' + (p.aura === 'legendary' ? '⚜ legendary' : '◈ set bonus') : ''}</span></div></div>`;
    html += '<div class="pd-col">' + PD_RIGHT.map(sl => pdSocket(sl, eq[sl])).join('') + '</div>';
    html += '</div><div class="pd-row">' + PD_BOTTOM.concat(extra).map(sl => pdSocket(sl, eq[sl])).join('') + '</div>';

    html += '<div style="color:#e8c168;margin:10px 0 4px;letter-spacing:1px">— CARRIED —</div><div class="inv-grid">';
    const inv = p.inventory || [];
    if (!inv.length) html += '<div class="slot">empty-handed</div>';
    inv.forEach((item, i) => {
      html += `<div class="inv-cell" data-i="${i}" data-cmd="wear ${MH.mobKeyword(item.name)}" title="${item.name} (${item.item_type || 'item'})">`
        + `<canvas width="34" height="34"></canvas><span class="inv-nm">${(item.short || item.name).slice(0, 26)}</span></div>`;
    });
    html += '</div>';
    els.invBody.innerHTML = html;

    const model = els.invBody.querySelector('#pd-model');
    if (model) drawCharModel(model, p);
    els.invBody.querySelectorAll('.pd-socket').forEach(el => {
      const item = eq[el.dataset.slot];
      if (item && MH.itemIcons) MH.itemIcons.intoCanvas(el.querySelector('canvas'), item);
      if (el.dataset.cmd) el.addEventListener('click', () => {
        MH.sendCommand(el.dataset.cmd);
        setTimeout(() => { MH.refreshState().then(renderInventory); }, 600);
      });
    });
    els.invBody.querySelectorAll('.inv-cell').forEach(el => {
      const item = inv[Number(el.dataset.i)];
      if (item && MH.itemIcons) MH.itemIcons.intoCanvas(el.querySelector('canvas'), item);
      el.addEventListener('click', () => {
        let cmd = el.dataset.cmd;
        if ((item.item_type || item.type) === 'weapon') cmd = cmd.replace('wear ', 'wield ');
        else if (['potion', 'food', 'drink', 'scroll'].includes(item.item_type || item.type)) cmd = cmd.replace('wear ', 'use ');
        MH.sendCommand(cmd);
        setTimeout(() => { MH.refreshState().then(renderInventory); }, 600);
      });
    });
  }

  function renderSpells() {
    const p = MH.state.player;
    if (!p) { els.spellsBody.textContent = 'No data yet.'; return; }
    const skills = p.skills || {};
    let html = '<div class="slot" style="margin-bottom:8px">click to use · drag onto the action bar to bind · keys 1–0</div>';
    const section = (title, entries, isSpell) => {
      let h = `<div style="color:#e8c168;letter-spacing:1px;margin:6px 0 4px">${title}</div><div class="spellgrid">`;
      if (!entries.length) h += '<div class="slot">none</div>';
      for (const s of entries) {
        const pretty = s.replace(/_/g, ' ');
        const cmd = isSpell ? `cast '${pretty}'` : pretty;
        const pct = skills[s] != null ? skills[s] : null;
        const prof = pct != null ? `<span class="prof">${pct}%</span>` : '';
        const bar = pct != null ? `<i class="prof-bar" style="position:absolute;left:30px;right:26px;bottom:2px"><b style="width:${pct}%"></b></i>` : '';
        h += `<div class="spell-entry" draggable="true" data-cmd="${cmd}" data-help="${pretty}" data-kind="${isSpell ? 'sparkle' : 'star'}">`
          + `<canvas width="20" height="20"></canvas><span class="nm">${pretty}</span>${prof}`
          + `<span class="helpq" title="help: ${pretty}">ⓘ</span>${bar}</div>`;
      }
      return h + '</div>';
    };
    html += section('SKILLS', p.class_skills || [], false);
    html += section('SPELLS', p.class_spells || [], true);
    els.spellsBody.innerHTML = html;
    els.spellsBody.querySelectorAll('.spell-entry').forEach(el => {
      drawIcon(el.querySelector('canvas'), el.dataset.kind);
      const q = el.querySelector('.helpq');
      if (q) q.addEventListener('click', async e => {
        e.stopPropagation();
        const lines = await (async () => { const pr = captureOutput(2200); MH.sendCommand(`help ${el.dataset.help}`, false); return pr; })();
        const text = lines.length ? lines.join('\n') : `No help entry for '${el.dataset.help}'.`;
        if (MH.immersion) MH.immersion.showDetailCard(el.dataset.help, text, 'detail');
      });
      el.addEventListener('click', () => {
        const t = currentTarget ? ` ${MH.mobKeyword(currentTarget.name)}` : '';
        MH.sendCommand(el.dataset.cmd + t);
        closeModals();
      });
      el.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', el.dataset.cmd);
        document.body.classList.add('skill-drag');   // backdrop must not eat the drop
      });
      el.addEventListener('dragend', () => document.body.classList.remove('skill-drag'));
    });
  }

  async function openTextPanel(cmd) {
    openModal('modal-journal');
    els.journalBody.textContent = '…';
    const p = captureOutput(1300);
    MH.sendCommand(cmd, false);
    const lines = await p;
    els.journalBody.textContent = lines.length ? lines.join('\n') : `(no response to '${cmd}')`;
  }

  // ---- help browser: searchable MUD help files in a panel ----
  async function openHelp(topic) {
    openModal('modal-journal');
    els.journalBody.innerHTML = '<div style="display:flex;gap:6px;margin-bottom:8px">'
      + '<input id="help-search" type="text" placeholder="search help… (e.g. fireball, stance, path)" '
      + 'style="flex:1;padding:6px 10px;background:rgba(13,15,21,.92);color:#d8dce8;border:1px solid rgba(140,150,180,.3);border-radius:6px;font-size:12px">'
      + '</div><pre id="help-text" style="white-space:pre-wrap;font-size:12px;line-height:1.5;margin:0">…</pre>';
    const input = document.getElementById('help-search');
    const out = document.getElementById('help-text');
    const show = async t => {
      out.textContent = '…';
      const pr = captureOutput(2400);
      MH.sendCommand(t ? `help ${t}` : 'help', false);
      const lines = await pr;
      out.textContent = lines.length ? lines.join('\n') : '(no help text came back)';
    };
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') show(input.value.trim());
      else if (e.key === 'Escape') { input.blur(); closeModals(); }
      e.stopPropagation();
    });
    await show(topic || '');
    if (!topic) input.focus();
  }

  // ---- persistent quest tracker: always-on objective HUD + minimap waypoint ----
  let qtMin = lsGet('mh_qt_min') === '1';
  let qtLastFetch = 0;
  const DIR_WORD = { north: 'N', south: 'S', east: 'E', west: 'W', up: 'up', down: 'down' };
  function refreshQuestTracker(force) {
    if (!MH.state.playerName) return;
    if (!force && Date.now() - qtLastFetch < 6000) return;
    qtLastFetch = Date.now();
    fetch(`/quests?player=${encodeURIComponent(MH.state.playerName)}`)
      .then(r => r.json()).then(renderQuestTracker).catch(() => {});
  }
  function renderQuestTracker(d) {
    const el = els.questTracker;
    if (!el) return;
    const active = (d.active || []).filter(q => !q.complete);
    const q = active[0] || (d.active || [])[0];
    if (!q) { el.classList.remove('show'); questWaypoint = null; return; }
    // waypoint: first incomplete visit/explore objective with a room target
    const way = q.objectives.find(o => !o.completed && /visit|explore|escort/.test(o.type || '') && typeof o.target === 'number');
    questWaypoint = way ? way.target : null;
    let objs = '';
    for (const o of q.objectives) {
      objs += `<div class="qt-obj ${o.completed ? 'done' : ''}"><span>${o.completed ? '✓' : '○'} ${o.description}</span>`
        + (o.required > 1 ? `<span class="qt-cnt">${o.current}/${o.required}</span>` : '') + `</div>`;
    }
    el.className = 'show' + (qtMin ? ' min' : '');
    el.innerHTML = `<div class="qt-hd"><span>📜 QUEST${active.length > 1 ? ` · ${active.length} active` : q.complete ? ' · READY' : ''}</span>`
      + `<span class="qt-min" id="qt-min" title="collapse">${qtMin ? '▸' : '▾'}</span></div>`
      + `<div class="qt-nm">${q.name}</div>${objs}`
      + (questWaypoint != null ? `<div class="qt-way">◈ objective marked on your map</div>` : (q.complete ? `<div class="qt-way" style="color:#6fd685">✓ return to the quest giver</div>` : ''));
    const m = document.getElementById('qt-min');
    if (m) m.addEventListener('click', () => { qtMin = !qtMin; lsSet('mh_qt_min', qtMin ? '1' : '0'); el.classList.toggle('min', qtMin); m.textContent = qtMin ? '▸' : '▾'; });
    renderMinimap();
  }

  function rewardText(r) {
    if (!r) return '';
    const parts = [];
    if (r.exp) parts.push(`${r.exp} XP`);
    if (r.gold) parts.push(`${r.gold} gold`);
    if (r.items && r.items.length) parts.push(`${r.items.length} item${r.items.length === 1 ? '' : 's'}`);
    if (r.respec) parts.push('respec');
    return parts.join(' · ');
  }
  async function openJournal() {
    openModal('modal-journal');
    els.journalBody.innerHTML = '<div class="slot">Consulting your journal…</div>';
    let d;
    try {
      d = await (await fetch(`/quests?player=${encodeURIComponent(MH.state.playerName)}`)).json();
    } catch (_) {
      // fall back to raw text if the endpoint isn't there
      const p = captureOutput(1400); MH.sendCommand('quests', false);
      const lines = await p;
      els.journalBody.textContent = lines.length ? lines.join('\n') : 'The journal stays blank.';
      return;
    }
    let html = '';
    // available quests from NPCs in the room
    if (d.givers && d.givers.length) {
      html += `<div class="q-hd">✦ AVAILABLE HERE</div>`;
      for (const g of d.givers) {
        for (const o of g.offers) {
          const tag = o.daily ? '<span class="q-tag daily">DAILY</span>' : o.repeatable ? '<span class="q-tag rep">REPEATABLE</span>' : '';
          html += `<div class="q-card avail"><div class="q-row"><span class="q-nm">${o.name}</span>`
            + `<span class="q-lv">Lv ${o.level_min}-${o.level_max}</span>${tag}</div>`
            + `<div class="q-from">from ${g.name}</div>`
            + `<div class="q-desc">${o.description}</div>`
            + `<div class="q-foot"><span class="q-rew">🎁 ${rewardText(o.rewards) || 'glory'}</span>`
            + `<button class="q-accept" data-q="${o.id}">ACCEPT</button></div></div>`;
        }
      }
    }
    // active quests
    html += `<div class="q-hd">📜 ACTIVE QUESTS${d.active.length ? ` (${d.active.length})` : ''}</div>`;
    if (!d.active.length) html += `<div class="alm-note" style="text-align:left">No active quests. Look for ✦ markers over NPCs, or check the Quest Board in Temple Square.</div>`;
    for (const q of d.active) {
      let objs = '';
      for (const o of q.objectives) {
        const pct = o.required ? Math.round((o.current / o.required) * 100) : (o.completed ? 100 : 0);
        objs += `<div class="q-obj ${o.completed ? 'done' : ''}"><span>${o.completed ? '✓' : '○'} ${o.description}</span>`
          + `<span class="q-cnt">${o.current}/${o.required}</span></div>`
          + `<div class="alm-prog"><i style="width:${pct}%"></i></div>`;
      }
      const timer = q.remaining_min != null ? `<span class="q-timer">⏳ ${q.remaining_min}m</span>` : '';
      html += `<div class="q-card ${q.complete ? 'complete' : ''}"><div class="q-row"><span class="q-nm">${q.name}</span>`
        + (q.complete ? '<span class="q-tag done">READY TO TURN IN</span>' : '') + timer + `</div>`
        + `<div class="q-desc">${q.description}</div>${objs}`
        + `<div class="q-foot"><span class="q-rew">🎁 ${rewardText(q.rewards) || ''}</span>`
        + `<button class="q-abandon" data-q="${q.id}">ABANDON</button></div></div>`;
    }
    els.journalBody.innerHTML = html;
    els.journalBody.querySelectorAll('.q-accept').forEach(b => b.addEventListener('click', () => {
      MH.sendCommand(`quest accept ${b.dataset.q}`, false); flash('Quest accepted'); setTimeout(openJournal, 700);
    }));
    els.journalBody.querySelectorAll('.q-abandon').forEach(b => b.addEventListener('click', () => {
      MH.sendCommand(`quest abandon ${b.dataset.q}`, false); flash('Quest abandoned'); setTimeout(openJournal, 700);
    }));
  }

  // ---- shop window: BUY/SELL tabs, icons, exact prices off /shop ----
  let shopKeeperName = null, shopTab = 'buy', shopData = null;
  async function openShop(keeper) {
    shopKeeperName = keeper ? keeper.name : null;
    shopTab = 'buy';
    openModal('modal-shop');
    els.shopBody.innerHTML = '<div class="slot">opening the wares…</div>';
    await shopFetchRender();
  }
  async function shopFetchRender() {
    try {
      const r = await fetch(`/shop?player=${encodeURIComponent(MH.state.playerName)}&keeper=${encodeURIComponent(shopKeeperName ? MH.mobKeyword(shopKeeperName) : '')}`);
      shopData = await r.json();
    } catch (_) { shopData = null; }
    if (!shopData || !shopData.found) { els.shopBody.innerHTML = '<div class="slot">No wares on offer here.</div>'; return; }
    renderShop();
  }
  function renderShop() {
    const d = shopData;
    let html = `<div class="shop-top"><span class="sk-name">${d.keeper}</span>`
      + `<span class="shop-tabs"><span class="stab ${shopTab === 'buy' ? 'on' : ''}" data-t="buy">BUY</span>`
      + `<span class="stab ${shopTab === 'sell' ? 'on' : ''}" data-t="sell">SELL</span></span>`
      + `<span class="shop-gold">🪙 ${d.gold}</span></div><div class="shop-list">`;
    const rows = shopTab === 'buy' ? d.buy : d.sell.filter(it => it.will_buy !== false);
    if (!rows.length) html += `<div class="slot">${shopTab === 'buy' ? 'Nothing for sale.' : 'Nothing they want to buy.'}</div>`;
    rows.forEach((it, i) => {
      const rc = it.set_id ? '#4ad0c0' : ({ uncommon: '#5fc46a', rare: '#5a8ae8', epic: '#b06ce0', legendary: '#ffa838' })[it.rarity] || '#d8dce8';
      const afford = shopTab === 'sell' || it.price <= d.gold;
      html += `<div class="shop-row ${afford ? '' : 'poor'}" data-i="${i}">`
        + `<canvas width="30" height="30"></canvas>`
        + `<span class="sr-nm" style="color:${rc}">${it.short || it.name}</span>`
        + `<span class="sr-price">${it.price} 🪙</span></div>`;
    });
    html += '</div>';
    els.shopBody.innerHTML = html;
    els.shopBody.querySelectorAll('.stab').forEach(t => t.addEventListener('click', () => { shopTab = t.dataset.t; renderShop(); }));
    els.shopBody.querySelectorAll('.shop-row').forEach(row => {
      const it = rows[Number(row.dataset.i)];
      if (MH.itemIcons) MH.itemIcons.intoCanvas(row.querySelector('canvas'), it);
      row.addEventListener('click', async () => {
        const verb = shopTab === 'buy' ? 'buy' : 'sell';
        const pr = captureOutput(1400);
        MH.sendCommand(`${verb} ${MH.mobKeyword(it.name)}`, false);
        const lines = await pr;
        if (lines.length) flash(lines[0].replace(/\x1b\[[0-9;]*m/g, ''));
        await MH.refreshState();
        await shopFetchRender();
      });
    });
  }

  // ---- training window: practice your craft at a trainer ----
  async function openTraining() {
    openModal('modal-shop');
    els.shopBody.innerHTML = '<div class="slot">the trainer sizes you up…</div>';
    await trainingRender();
  }
  async function trainingRender() {
    let d = null;
    try {
      const r = await fetch(`/training?player=${encodeURIComponent(MH.state.playerName)}`);
      d = await r.json();
    } catch (_) { /* server too old */ }
    if (!d || !d.found) { els.shopBody.innerHTML = '<div class="slot">No training to be had.</div>'; return; }
    let html = `<div class="shop-top"><span class="sk-name">TRAINING</span>`
      + `<span class="shop-gold">✦ ${d.practices} practice${d.practices === 1 ? '' : 's'} · 🪙 ${d.gold}</span></div>`;
    const section = (title, list, kind) => {
      if (!list.length) return '';
      let h = `<div class="train-head">${title}</div><div class="shop-list">`;
      for (const a of list) {
        const pretty = a.id.replace(/_/g, ' ');
        const mastered = a.prof >= 85;
        h += `<div class="shop-row train ${mastered ? 'mastered' : ''}" data-id="${a.id}" data-kind="${kind}" `
          + `title="${mastered ? 'mastered' : 'practice (1 session)'}">`
          + `<canvas width="22" height="22" data-icon="${kind}"></canvas>`
          + `<span class="sr-nm">${pretty}</span>`
          + `<span class="tr-bar"><i style="width:${Math.min(100, a.prof)}%"></i></span>`
          + `<span class="sr-price">${mastered ? 'MASTERED' : a.prof + '%'}</span></div>`;
      }
      return h + '</div>';
    };
    html += section('SKILLS', d.skills, 'star');
    html += section('SPELLS', d.spells, 'sparkle');
    els.shopBody.innerHTML = html;
    els.shopBody.querySelectorAll('.shop-row.train').forEach(row => {
      drawIcon(row.querySelector('canvas'), row.querySelector('canvas').dataset.icon);
      if (!row.classList.contains('mastered')) row.addEventListener('click', async () => {
        const pr = captureOutput(1400);
        MH.sendCommand(`practice ${row.dataset.id.replace(/_/g, ' ')}`, false);
        const lines = await pr;
        if (lines.length) flash(lines[lines.length - 1].replace(/\x1b\[[0-9;]*m/g, ''));
        await trainingRender();
      });
    });
  }

  // ---- almanac: daily rewards, achievements, titles, collections ----
  let almTab = 'daily', almCat = 'all', almData = null;
  async function openAlmanac(tab) {
    almTab = tab || 'daily';
    openModal('modal-almanac');
    document.querySelectorAll('#modal-almanac .mtab').forEach(t => t.classList.toggle('active', t.dataset.atab === almTab));
    els.almanacBody.innerHTML = '<div class="slot">consulting the almanac…</div>';
    try {
      almData = await (await fetch(`/almanac?player=${encodeURIComponent(MH.state.playerName)}`)).json();
    } catch (_) { els.almanacBody.innerHTML = '<div class="slot">almanac unavailable</div>'; return; }
    renderAlmanac();
  }
  function renderAlmanac() {
    if (!almData) return;
    const b = els.almanacBody;
    if (almTab === 'daily') {
      const d = almData.daily;
      let days = '<div class="alm-streak">';
      for (let i = 1; i <= 7; i++) {
        const done = i < d.streak_day || (i === d.streak_day && d.claimed_today);
        const today = i === d.streak_day;
        const r = (i === 7) ? '🎁' : '';
        days += `<div class="alm-day ${done ? 'done' : ''} ${today ? 'today' : ''}">`
          + `${done ? '<span class="dchk">✓</span>' : ''}`
          + `<div class="dn">DAY ${i}</div><div class="dr">${r || ''}</div></div>`;
      }
      days += '</div>';
      const claim = d.claimed_today
        ? `<div class="alm-claim done">✓ Today's reward claimed — come back tomorrow</div>`
        : `<div class="alm-claim" id="alm-claim">🌟 Claim daily reward: +${d.today.gold} gold · +${d.today.xp} XP</div>`;
      const ms = d.next_milestone ? `<div class="alm-note">🎁 Milestone at day ${d.next_milestone.day}: ${d.next_milestone.name}</div>` : '';
      b.innerHTML = `<div class="alm-daily">`
        + `<div class="alm-hd">🔥 Login streak: ${d.streak} day${d.streak === 1 ? '' : 's'} · ${d.total_days} total visits</div>`
        + days + claim
        + `<div class="alm-note">Tomorrow: +${d.next.gold} gold · +${d.next.xp} XP — keep the streak alive!</div>`
        + ms + `</div>`;
      const cb = document.getElementById('alm-claim');
      if (cb) cb.addEventListener('click', async () => {
        cb.textContent = 'claiming…';
        MH.sendCommand('daily', false);
        setTimeout(() => openAlmanac('daily'), 700);
      });
    } else if (almTab === 'achievements') {
      const a = almData.achievements;
      const cats = ['all', ...Array.from(new Set(a.list.map(x => x.category)))];
      let html = `<div class="alm-hd">★ ${a.points}/${a.max_points} points · ${a.unlocked}/${a.total} unlocked</div>`;
      html += '<div class="alm-cats">' + cats.map(cn =>
        `<span class="alm-cat ${cn === almCat ? 'on' : ''}" data-cat="${cn}">${cn.toUpperCase()}</span>`).join('') + '</div>';
      const list = a.list.filter(x => almCat === 'all' || x.category === almCat)
        .sort((x, y) => (y.unlocked - x.unlocked) || (y.points - x.points));
      html += '<div class="alm-grid">';
      for (const x of list) {
        const bar = x.target ? `<div class="alm-prog"><i style="width:${Math.round((x.progress / x.target) * 100)}%"></i></div>` : '';
        const tl = x.reward_title ? `<div class="at">🏷 ${x.reward_title}</div>` : '';
        html += `<div class="alm-ach ${x.unlocked ? 'done' : 'locked'}">`
          + `<div class="ai">${x.icon}</div><div class="am">`
          + `<div class="an">${x.name}<span class="pts">+${x.points}</span></div>`
          + `<div class="ad">${x.description}</div>`
          + (x.unlocked ? '' : (x.target ? `<div class="ad" style="color:#7a8094">${x.progress}/${x.target}</div>${bar}` : ''))
          + tl + `</div></div>`;
      }
      html += '</div>';
      b.innerHTML = html;
      b.querySelectorAll('.alm-cat').forEach(c => c.addEventListener('click', () => { almCat = c.dataset.cat; renderAlmanac(); }));
    } else if (almTab === 'titles') {
      const t = almData.titles;
      let html = `<div class="alm-hd">🏷 Choose your displayed title</div><div class="alm-titles">`;
      html += `<div class="alm-title ${t.current === 'the Adventurer' ? 'current' : ''}" data-title="none">the Adventurer <small style="color:#8a90a4">(default)</small></div>`;
      if (!t.available.length) html += `<div class="alm-note" style="margin-top:6px">Earn achievements to unlock titles.</div>`;
      for (const ti of t.available) html += `<div class="alm-title ${ti === t.current ? 'current' : ''}" data-title="${ti}">${ti}</div>`;
      html += '</div>';
      b.innerHTML = html;
      b.querySelectorAll('.alm-title').forEach(el => el.addEventListener('click', () => {
        MH.sendCommand(`title ${el.dataset.title}`, false);
        flash(`Title set: ${el.dataset.title === 'none' ? 'the Adventurer' : el.dataset.title}`);
        setTimeout(() => openAlmanac('titles'), 600);
      }));
    } else if (almTab === 'collections') {
      const cs = almData.collections || [];
      const gs = almData.gear_sets || [];
      let html = `<div class="alm-hd">📚 Collections</div>`;
      if (!cs.length) html += `<div class="alm-note">No collections tracked yet.</div>`;
      for (const c of cs) {
        const complete = c.have >= c.total && c.total > 0;
        const rw = c.reward || {};
        const rwt = [rw.gold ? `${rw.gold}g` : '', rw.exp ? `${rw.exp}xp` : '', rw.title ? `“${rw.title}”` : ''].filter(Boolean).join(' · ');
        html += `<div class="alm-coll ${complete ? 'complete' : ''}"><div class="cn"><b>${c.name}</b>`
          + `<small>${c.description}${rwt ? ' — reward: ' + rwt : ''}</small></div>`
          + `<div class="cc">${complete ? '✓ complete' : c.have + '/' + c.total}</div></div>`;
      }
      html += `<div class="alm-hd" style="margin-top:12px">🛡 GEAR SETS</div>`;
      if (!gs.length) html += `<div class="alm-note">You own no set pieces yet. Matching armor unlocks set bonuses.</div>`;
      for (const s of gs) {
        const tiers = s.tiers.map(t => `<div class="alm-ach ${t.active ? 'done' : 'locked'}" style="padding:5px 8px"><div class="am"><div class="ad" style="color:${t.active ? '#8ce8a0' : '#9aa0b4'}">${t.active ? '✓' : `${t.need}pc`} ${t.text}</div></div></div>`).join('');
        html += `<div class="alm-coll" style="flex-direction:column;align-items:stretch"><div class="cn" style="display:flex"><b style="flex:1">${s.name}</b>`
          + `<span class="cc">worn ${s.worn}/${s.total} · own ${s.owned}/${s.total}</span></div>`
          + `<div style="display:flex;flex-direction:column;gap:3px;margin-top:5px">${tiers}</div></div>`;
      }
      b.innerHTML = html;
    }
  }

  // ---- services: mail / bank / storage ----
  let svTab = 'mail', svData = null;
  async function openServices(tab) {
    svTab = tab || 'mail';
    openModal('modal-services');
    document.querySelectorAll('#modal-services .mtab').forEach(t => t.classList.toggle('active', t.dataset.stab === svTab));
    els.servicesBody.innerHTML = '<div class="slot">…</div>';
    try {
      svData = await (await fetch(`/services?player=${encodeURIComponent(MH.state.playerName)}`)).json();
    } catch (_) { els.servicesBody.innerHTML = '<div class="slot">services unavailable</div>'; return; }
    renderServices();
  }
  function renderServices() {
    if (!svData) return;
    const b = els.servicesBody;
    if (svTab === 'mail') {
      const m = svData.mail;
      let html = `<div class="sv-hd">✉ INBOX · ${m.unread} unread / ${m.messages.length} total</div><div class="sv-mail">`;
      if (!m.messages.length) html += `<div class="alm-note" style="text-align:left">No mail. Send a letter below — it reaches any player, online or not.</div>`;
      for (const msg of m.messages.slice().reverse()) {
        html += `<div class="sv-msg ${msg.read ? '' : 'unread'}"><div class="mh">`
          + `<span class="ms">${msg.read ? '' : '<span class="dot">●</span>'}${msg.sender}</span>`
          + `<span class="mt">${msg.ts}</span><span class="md" data-del="${msg.id}">delete</span></div>`
          + `<div class="mb">${msg.body.replace(/</g, '&lt;')}</div></div>`;
      }
      html += `</div><div class="sv-compose"><input class="to" id="sv-to" placeholder="to (name)">`
        + `<input class="body" id="sv-body" placeholder="message…"><button class="sv-btn" id="sv-send">SEND</button></div>`;
      b.innerHTML = html;
      b.querySelectorAll('.md').forEach(d => d.addEventListener('click', () => {
        MH.sendCommand(`mail delete ${d.dataset.del}`, false); setTimeout(() => openServices('mail'), 500);
      }));
      const send = () => {
        const to = document.getElementById('sv-to').value.trim();
        const body = document.getElementById('sv-body').value.trim();
        if (!to || !body) return;
        MH.sendCommand(`mail send ${to} ${body}`, false); flash(`Mail sent to ${to}`);
        setTimeout(() => openServices('mail'), 600);
      };
      document.getElementById('sv-send').addEventListener('click', send);
      ['sv-to', 'sv-body'].forEach(id => document.getElementById(id).addEventListener('keydown', e => {
        e.stopPropagation(); if (e.key === 'Enter') send();
      }));
      // reading marks unread as read server-side; nudge a read so badges clear
      if (m.unread) MH.sendCommand('mail read', false);
    } else if (svTab === 'bank') {
      const bk = svData.bank;
      let html = `<div class="sv-hd">🏛 BANK OF MISTHOLLOW</div>`;
      if (!bk.at_bank) html += `<div class="sv-gate">You can view your balance anywhere, but must stand in a bank to move gold.</div>`;
      html += `<div class="sv-bank"><div class="sv-coin">`
        + `<div class="c"><div class="lbl">VAULT</div><div class="amt">${bk.balance.toLocaleString()}</div></div>`
        + `<div class="c"><div class="lbl">ON HAND</div><div class="amt">${bk.on_hand.toLocaleString()}</div></div></div>`;
      const dis = bk.at_bank ? '' : 'disabled';
      html += `<div class="sv-row"><input id="sv-amt" type="number" min="1" placeholder="amount" ${dis}>`
        + `<button class="sv-btn ${bk.at_bank ? '' : 'dim'}" id="sv-dep" ${dis}>DEPOSIT</button>`
        + `<button class="sv-btn ${bk.at_bank ? '' : 'dim'}" id="sv-wd" ${dis}>WITHDRAW</button></div>`;
      if (bk.at_bank) html += `<div class="sv-row"><button class="sv-btn" id="sv-depall" style="flex:1">DEPOSIT ALL ON HAND</button></div>`;
      html += `</div>`;
      b.innerHTML = html;
      if (bk.at_bank) {
        const amt = () => document.getElementById('sv-amt').value.trim();
        document.getElementById('sv-dep').addEventListener('click', () => { if (amt()) { MH.sendCommand(`deposit ${amt()}`, false); setTimeout(() => openServices('bank'), 500); } });
        document.getElementById('sv-wd').addEventListener('click', () => { if (amt()) { MH.sendCommand(`withdraw ${amt()}`, false); setTimeout(() => openServices('bank'), 500); } });
        document.getElementById('sv-depall').addEventListener('click', () => { MH.sendCommand(`deposit ${bk.on_hand}`, false); setTimeout(() => openServices('bank'), 500); });
      }
    } else if (svTab === 'storage') {
      const s = svData.storage;
      let html = `<div class="sv-hd">📦 STORAGE LOCKER${s.location ? ' · ' + s.location : ''}</div>`;
      if (!s.at_inn) html += `<div class="sv-gate">Find an innkeeper to store or retrieve items.</div>`;
      html += `<div class="sv-store">`;
      if (!s.items.length) html += `<div class="alm-note" style="text-align:left">Locker empty.</div>`;
      for (const it of s.items) {
        html += `<div class="sv-item"><span class="nm">${it.name}</span>`
          + (s.at_inn ? `<button class="sv-btn" data-ret="${it.name.replace(/"/g, '')}">RETRIEVE</button>` : '') + `</div>`;
      }
      html += `</div>`;
      if (s.at_inn) html += `<div class="sv-compose"><input class="body" id="sv-stitem" placeholder="store item from inventory by name…"><button class="sv-btn" id="sv-store">STORE</button></div>`;
      b.innerHTML = html;
      if (s.at_inn) {
        b.querySelectorAll('[data-ret]').forEach(btn => btn.addEventListener('click', () => {
          MH.sendCommand(`retrieve ${btn.dataset.ret.split(' ').slice(-1)[0]}`, false); setTimeout(() => openServices('storage'), 500);
        }));
        const st = document.getElementById('sv-store');
        st.addEventListener('click', () => { const v = document.getElementById('sv-stitem').value.trim(); if (v) { MH.sendCommand(`store ${v}`, false); setTimeout(() => openServices('storage'), 500); } });
        document.getElementById('sv-stitem').addEventListener('keydown', e => e.stopPropagation());
      }
    }
  }

  // ---- stable: pets / companions / mounts ----
  let stTab = 'pets', stData = null;
  async function openStable(tab) {
    stTab = tab || 'pets';
    openModal('modal-stable');
    document.querySelectorAll('#modal-stable .mtab').forEach(t => t.classList.toggle('active', t.dataset.ctab === stTab));
    els.stableBody.innerHTML = '<div class="slot">…</div>';
    try {
      stData = await (await fetch(`/stable?player=${encodeURIComponent(MH.state.playerName)}`)).json();
    } catch (_) { els.stableBody.innerHTML = '<div class="slot">stable unavailable</div>'; return; }
    renderStable();
  }
  function hpbar(hp, max) { return `<div class="st-hp"><i style="width:${Math.max(0, Math.min(100, (hp / Math.max(1, max)) * 100))}%"></i></div>`; }
  function renderStable() {
    if (!stData) return;
    const b = els.stableBody;
    if (stTab === 'pets') {
      let html = `<div class="st-hd">🐾 SUMMONED & UNDEAD PETS</div>`;
      if (!stData.pets.length) html += `<div class="alm-note" style="text-align:left">No active pets. Casters summon them; necromancers raise them.</div>`;
      for (const p of stData.pets) {
        const ab = p.abilities && p.abilities.length ? `<div class="st-d">✦ ${p.abilities.map(a => a.replace(/_/g, ' ')).join(', ')}</div>` : '';
        html += `<div class="st-card"><div class="st-ic">🐾</div><div class="st-m">`
          + `<div class="st-n">${p.name}<span class="tag">L${p.level} · ${p.type} · loyalty ${p.loyalty}%</span></div>`
          + hpbar(p.hp, p.maxHp) + ab + `</div>`
          + `<button class="st-btn" data-dismiss="${p.name.split(' ').slice(-1)[0]}">DISMISS</button></div>`;
      }
      b.innerHTML = html;
      b.querySelectorAll('[data-dismiss]').forEach(btn => btn.addEventListener('click', () => {
        MH.sendCommand(`dismiss ${btn.dataset.dismiss}`, false); setTimeout(() => openStable('pets'), 500);
      }));
    } else if (stTab === 'companions') {
      let html = `<div class="st-hd">🛡 HIRED COMPANIONS</div>`;
      if (!stData.companions.length) html += `<div class="alm-note" style="text-align:left">No companions hired. Find a mercenary or recruit and 'hire' them.</div>`;
      for (const cmp of stData.companions) {
        html += `<div class="st-card"><div class="st-ic">${cmp.role === 'Healer' ? '✚' : cmp.role === 'Mage' ? '✦' : cmp.role === 'Rogue' ? '🗡' : '🛡'}</div><div class="st-m">`
          + `<div class="st-n">${cmp.name}<span class="tag">L${cmp.level} · ${cmp.role}</span></div>${hpbar(cmp.hp, cmp.maxHp)}</div>`
          + `<button class="st-btn" data-dismiss="${cmp.name.split(' ').slice(-1)[0]}">DISMISS</button></div>`;
      }
      b.innerHTML = html;
      b.querySelectorAll('[data-dismiss]').forEach(btn => btn.addEventListener('click', () => {
        MH.sendCommand(`dismiss ${btn.dataset.dismiss}`, false); setTimeout(() => openStable('companions'), 500);
      }));
    } else if (stTab === 'mounts') {
      const m = stData.mounts;
      let html = `<div class="st-hd">🐴 YOUR MOUNTS</div>`;
      if (!m.owned.length) html += `<div class="alm-note" style="text-align:left">You own no mounts.</div>`;
      for (const o of m.owned) {
        const feats = [o.can_fly ? 'flight' : '', o.combat_ok ? 'combat-ready' : '', `+${Math.round(o.speed_bonus * 100)}% speed`].filter(Boolean).join(' · ');
        html += `<div class="st-card ${o.active ? 'active' : ''}"><div class="st-ic">${o.can_fly ? '🦅' : '🐴'}</div><div class="st-m">`
          + `<div class="st-n">${o.name}${o.active ? '<span class="tag">riding</span>' : ''}</div><div class="st-d">${feats}</div></div>`
          + (o.active ? `<button class="st-btn" id="st-dismount">DISMOUNT</button>`
                      : `<button class="st-btn go" data-mount="${o.key}">RIDE</button>`) + `</div>`;
      }
      html += `<div class="st-hd">🏪 STABLE${m.at_stable ? '' : ' (find a stable to buy)'}</div>`;
      for (const pu of m.purchasable) {
        const can = m.at_stable && pu.afford;
        html += `<div class="st-card"><div class="st-ic">${pu.can_fly ? '🦅' : '🐴'}</div><div class="st-m">`
          + `<div class="st-n">${pu.name}</div><div class="st-d">${pu.description}</div></div>`
          + `<span class="st-cost ${pu.afford ? '' : 'poor'}">${pu.cost.toLocaleString()}g</span>`
          + `<button class="st-btn ${can ? 'go' : 'dim'}" data-buy="${pu.key}" ${can ? '' : 'disabled'}>BUY</button></div>`;
      }
      b.innerHTML = html;
      const dm = document.getElementById('st-dismount');
      if (dm) dm.addEventListener('click', () => { MH.sendCommand('dismount', false); setTimeout(() => openStable('mounts'), 500); });
      b.querySelectorAll('[data-mount]').forEach(btn => btn.addEventListener('click', () => { MH.sendCommand(`mount ${btn.dataset.mount}`, false); setTimeout(() => openStable('mounts'), 500); }));
      b.querySelectorAll('[data-buy]').forEach(btn => btn.addEventListener('click', () => { MH.sendCommand(`stable buy ${btn.dataset.buy}`, false); setTimeout(() => openStable('mounts'), 600); }));
    }
  }

  // ---- legend: prestige + leaderboards ----
  let lgTab = 'prestige', lgCat = 'level', lgData = null, lgConfirm = null;
  async function openLegend(tab) {
    lgTab = tab || 'prestige';
    openModal('modal-legend');
    document.querySelectorAll('#modal-legend .mtab').forEach(t => t.classList.toggle('active', t.dataset.ltab === lgTab));
    els.legendBody.innerHTML = '<div class="slot">…</div>';
    try {
      lgData = await (await fetch(`/legend?player=${encodeURIComponent(MH.state.playerName)}`)).json();
    } catch (_) { els.legendBody.innerHTML = '<div class="slot">legend unavailable</div>'; return; }
    renderLegend();
  }
  function renderLegend() {
    if (!lgData) return;
    const b = els.legendBody;
    if (lgTab === 'prestige') {
      const p = lgData.prestige;
      let html = '';
      if (p.current) {
        html += `<div class="lg-cur"><div class="nm">★ ${p.current_name}</div>`
          + `<div class="od" style="color:#c8ccd8">Your ${p.base_class} has ascended. Prestige abilities are active and you can level to 60.</div></div>`;
      } else if (!p.eligible) {
        html += `<div class="lg-gate">Reach level 50 to choose a prestige specialization. You are level ${p.level}.</div>`;
      } else {
        html += `<div class="lg-hd">★ CHOOSE YOUR PRESTIGE PATH (level 50+)</div>`;
      }
      for (const o of p.options) {
        const ab = o.abilities.map(a => `<div class="lg-ab"><b>${a.name}</b> — ${a.description}</div>`).join('');
        const isCur = p.current === o.key;
        html += `<div class="lg-opt"><div class="oh"><span class="on">${o.name}</span>`
          + `<span class="oth">${o.theme}</span></div><div class="od">${o.description}</div>${ab}`
          + (!p.current && p.eligible ? `<button class="lg-pick ${lgConfirm === o.key ? 'confirm' : ''}" data-spec="${o.key}" data-name="${o.name}">${lgConfirm === o.key ? 'CONFIRM — this is permanent' : 'SPECIALIZE'}</button>` : '')
          + (isCur ? '<div class="lg-ab" style="color:#8ce8a0">✓ your current path</div>' : '')
          + `</div>`;
      }
      b.innerHTML = html;
      b.querySelectorAll('[data-spec]').forEach(btn => btn.addEventListener('click', () => {
        const key = btn.dataset.spec, name = btn.dataset.name;
        if (lgConfirm === key) { MH.sendCommand(`specialize ${name}`, false); MH.sendCommand(`specialize ${name}`, false); flash(`Ascending as ${name}…`); lgConfirm = null; setTimeout(() => openLegend('prestige'), 900); }
        else { lgConfirm = key; renderLegend(); }
      }));
    } else if (lgTab === 'leaderboards') {
      const cats = ['level', 'kills', 'gold', 'achievements', 'quests'];
      const lbl = { level: '⚔️ Level', kills: '💀 Kills', gold: '💰 Wealth', achievements: '🏆 Achievements', quests: '📜 Quests' };
      let html = '<div class="lg-cats">' + cats.map(c => `<span class="lg-cat ${c === lgCat ? 'on' : ''}" data-lc="${c}">${lbl[c]}</span>`).join('') + '</div>';
      const bd = lgData.leaderboards[lgCat] || { top: [], my_rank: null, total: 0 };
      const medal = i => i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : (i + 1) + '.';
      const me = (MH.state.playerName || '').toLowerCase();
      for (let i = 0; i < bd.top.length; i++) {
        const r = bd.top[i];
        html += `<div class="lg-rank ${r.name.toLowerCase() === me ? 'me' : ''}"><span class="pos">${medal(i)}</span>`
          + `<span class="rn">${r.name}</span><span class="rv">${(r.value || 0).toLocaleString()}</span></div>`;
      }
      if (!bd.top.length) html += `<div class="alm-note">No ranked players yet.</div>`;
      html += `<div class="lg-myrank">${bd.my_rank ? `Your rank: #${bd.my_rank} of ${bd.total}` : 'Unranked — play on to climb the boards!'}</div>`;
      b.innerHTML = html;
      b.querySelectorAll('.lg-cat').forEach(c => c.addEventListener('click', () => { lgCat = c.dataset.lc; renderLegend(); }));
    }
  }

  // ---- minimap + click-to-walk ----
  const MM_OFFSETS = { north: [0, -1, 0], south: [0, 1, 0], east: [1, 0, 0], west: [-1, 0, 0], up: [0, 0, 1], down: [0, 0, -1] };
  let mmLarge = false;
  let walkTargetVnum = null;
  let questWaypoint = null;   // room vnum of the current tracked quest objective
  let mmZoom = Number(lsGet('misthollow_mm_zoom')) || 9;
  let mmZOffset = 0;   // 0 = your level; -1 peeks the sewers below, +1 above

  function mmCell() { return mmZoom + (mmLarge ? 3 : 0); }
  function mmSetZoom(z) {
    mmZoom = Phaser.Math ? Phaser.Math.Clamp(z, 5, 20) : Math.max(5, Math.min(20, z));
    lsSet('misthollow_mm_zoom', String(mmZoom));
    renderMinimap();
  }

  function renderMinimap() {
    const payload = MH.state.lastPayload;
    if (!payload || !payload.player || !els.minimap) return;
    const ctx = els.minimap.getContext('2d');
    const W = els.minimap.width, H = els.minimap.height;
    ctx.fillStyle = '#0b0c10';
    ctx.fillRect(0, 0, W, H);
    const p = payload.player;
    if (renderMinimap._lastPz !== (p.z || 0)) { renderMinimap._lastPz = (p.z || 0); mmZOffset = 0; }
    const z = (p.z || 0) + mmZOffset;
    const cell = mmCell();
    if (mmZOffset !== 0) {
      // peeking another level: faint echo of your own level for orientation
      ctx.globalAlpha = 0.14;
      ctx.fillStyle = '#6a7084';
      for (const r of (payload.rooms || [])) {
        if ((r.z || 0) !== (p.z || 0)) continue;
        const ex = W / 2 + (r.x - p.x) * cell - (cell - 2) / 2;
        const ey = H / 2 + (r.y - p.y) * cell - (cell - 2) / 2;
        if (ex < -cell || ex > W || ey < -cell || ey > H) continue;
        ctx.fillRect(ex, ey, cell - 2, cell - 2);
      }
      ctx.globalAlpha = 1;
    }
    const zoneColor = {};
    (payload.zones || []).forEach(zn => { zoneColor[zn.id] = zn.color; });
    for (const r of (payload.rooms || [])) {
      if ((r.z || 0) !== z) continue;
      const x = W / 2 + (r.x - p.x) * cell - (cell - 2) / 2;
      const y = H / 2 + (r.y - p.y) * cell - (cell - 2) / 2;
      if (x < -cell || x > W || y < -cell || y > H) continue;
      ctx.fillStyle = r.vnum === walkTargetVnum ? '#e8c168' : (zoneColor[r.zone] || '#4a4f60');
      ctx.globalAlpha = r.vnum === p.vnum ? 1 : 0.55;
      ctx.fillRect(x, y, cell - 2, cell - 2);
      // up/down markers
      if ((r.exits || []).includes('up') || (r.exits || []).includes('down')) {
        ctx.fillStyle = '#c8ccd8';
        ctx.fillRect(x + (cell - 2) / 2 - 1, y + (cell - 2) / 2 - 1, 1, 1);
      }
    }
    ctx.globalAlpha = 0.6;
    ctx.fillStyle = '#7a8094';
    for (const f of (payload.frontier || [])) {
      if ((f.z || 0) !== z) continue;
      const x = W / 2 + (f.x - p.x) * cell;
      const y = H / 2 + (f.y - p.y) * cell;
      ctx.fillRect(x - 1, y - 1, 2, 2);
    }
    ctx.globalAlpha = 1;
    // quest waypoint: a gold diamond on the target room, or an edge arrow toward it
    if (questWaypoint != null) {
      const wr = (payload.rooms || []).find(r => r.vnum === questWaypoint);
      if (wr && (wr.z || 0) === z) {
        const wx = W / 2 + (wr.x - p.x) * cell, wy = H / 2 + (wr.y - p.y) * cell;
        ctx.fillStyle = '#ffd44a';
        ctx.beginPath(); ctx.moveTo(wx, wy - 4); ctx.lineTo(wx + 4, wy); ctx.lineTo(wx, wy + 4); ctx.lineTo(wx - 4, wy); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = 'rgba(255,212,74,0.5)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(wx, wy, 7, 0, 7); ctx.stroke();
      } else if (wr) {
        // off-level or off-screen: arrow from center toward it
        const ang = Math.atan2((wr.y - p.y), (wr.x - p.x));
        const ex = W / 2 + Math.cos(ang) * (W / 2 - 10), ey = H / 2 + Math.sin(ang) * (H / 2 - 10);
        ctx.save(); ctx.translate(ex, ey); ctx.rotate(ang);
        ctx.fillStyle = '#ffd44a'; ctx.beginPath(); ctx.moveTo(5, 0); ctx.lineTo(-3, -4); ctx.lineTo(-3, 4); ctx.closePath(); ctx.fill();
        ctx.restore();
      }
    }
    if (mmZOffset === 0) {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(W / 2 - 2, H / 2 - 2, 4, 4);
    } else {
      // hollow marker: you are not standing on the viewed level
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      ctx.strokeRect(W / 2 - 2.5, H / 2 - 2.5, 5, 5);
      ctx.fillStyle = '#e8c168';
      ctx.font = '8px Trebuchet MS, Verdana, sans-serif';
      ctx.fillText(mmZOffset < 0 ? '▼ below ground' : '▲ upper level', 4, H - 4);
    }
  }

  function bfsPath(fromVnum, toVnum) {
    const payload = MH.state.lastPayload;
    if (!payload) return null;
    const byVnum = new Map();
    const byCoord = new Map();
    for (const r of (payload.rooms || [])) {
      byVnum.set(r.vnum, r);
      byCoord.set(`${r.x},${r.y},${r.z || 0}`, r);
    }
    if (!byVnum.has(fromVnum) || !byVnum.has(toVnum)) return null;
    const prev = new Map([[fromVnum, null]]);
    const queue = [fromVnum];
    while (queue.length) {
      const v = queue.shift();
      if (v === toVnum) break;
      const room = byVnum.get(v);
      for (const dir of (room.exits || [])) {
        const off = MM_OFFSETS[dir];
        if (!off) continue;
        const nb = byCoord.get(`${room.x + off[0]},${room.y + off[1]},${(room.z || 0) + off[2]}`);
        if (!nb || prev.has(nb.vnum)) continue;
        prev.set(nb.vnum, { v, dir });
        queue.push(nb.vnum);
      }
      // named passages (gate/arch/portal) teleport across the grid
      for (const pe of (room.portals || [])) {
        const nb = byVnum.get(pe.to_room);
        if (!nb || prev.has(nb.vnum)) continue;
        prev.set(nb.vnum, { v, dir: pe.name });
        queue.push(nb.vnum);
      }
    }
    if (!prev.has(toVnum)) return null;
    const dirs = [];
    let cur = toVnum;
    while (prev.get(cur)) { dirs.unshift(prev.get(cur).dir); cur = prev.get(cur).v; }
    return dirs;
  }

  function walkStep() {
    if (walkTargetVnum == null) return;
    const p = MH.state.lastPayload && MH.state.lastPayload.player;
    if (!p) return;
    if (p.vnum === walkTargetVnum) { walkTargetVnum = null; renderMinimap(); flash('You arrive.'); return; }
    const dirs = bfsPath(p.vnum, walkTargetVnum);
    if (!dirs || !dirs.length) { walkTargetVnum = null; renderMinimap(); return; }
    setTimeout(() => MH.bus.emit('walk.step', dirs[0]), 300);
  }

  function cancelWalk() {
    if (walkTargetVnum != null) { walkTargetVnum = null; renderMinimap(); }
  }

  function minimapClick(e) {
    const payload = MH.state.lastPayload;
    if (!payload || !payload.player) return;
    const rect = els.minimap.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const cell = mmCell();
    const p = payload.player;
    const rx = Math.round((mx - els.minimap.width / 2) / cell + p.x);
    const ry = Math.round((my - els.minimap.height / 2) / cell + p.y);
    const room = (payload.rooms || []).find(r => r.x === rx && r.y === ry && (r.z || 0) === ((p.z || 0) + mmZOffset));
    if (!room || room.vnum === p.vnum) return;
    walkTargetVnum = room.vnum;
    renderMinimap();
    flash(`Walking to ${room.name}…`);
    walkStep();
  }

  // ---- world map (M): WoW-style world -> zone drill-down ----
  let wmOpen = false, wmView = 'world', wmZoneId = null, wmZ = 0;
  const DIRV = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };
  let wmHit = [];

  async function wmAtlas() {
    if (MH.state.atlas) return MH.state.atlas;
    try {
      const r = await fetch('/atlas');
      const a = await r.json();
      a.byVnum = new Map(a.rooms.map(rm => [rm.vnum, rm]));
      MH.state.atlas = a;
    } catch (_) { /* old server: fall back to explored-only */ }
    return MH.state.atlas;
  }
  function wmExplored() {
    const payload = MH.state.lastPayload;
    return new Set(((payload && payload.rooms) || []).map(r => r.vnum));
  }

  function wmToggle(force) {
    wmOpen = force != null ? force : !wmOpen;
    const el = $('world-map');
    if (!el) return;
    el.classList.toggle('show', wmOpen);
    setWorldInput(!wmOpen);
    if (wmOpen) {
      wmView = 'world';
      wmAtlas().then(() => requestAnimationFrame(wmRender));
    }
  }

  function wmRender() {
    const payload = MH.state.lastPayload;
    if (!payload || !payload.player) return;
    $('wm-world').style.display = wmView === 'world' ? '' : 'none';
    $('wm-zone').style.display = wmView === 'zone' ? '' : 'none';
    $('wm-tip').style.display = 'none';
    if (wmView === 'world') wmRenderWorld(payload);
    else wmRenderZone(payload);
  }

  function wmRenderWorld(payload) {
    const host = $('wm-world');
    const canvas = $('wm-zone');           // doubles as the road-line layer
    const body = $('wm-body');
    const rect = body.getBoundingClientRect();
    canvas.style.display = '';
    canvas.style.pointerEvents = 'none';      // cards take the clicks
    canvas.width = rect.width; canvas.height = rect.height;
    const lctx = canvas.getContext('2d');
    lctx.clearRect(0, 0, canvas.width, canvas.height);
    $('wm-crumb').innerHTML = '<span class="here">WORLD</span>';
    $('wm-levels').innerHTML = '';
    host.innerHTML = '';
    const atlas = MH.state.atlas;
    const explored = wmExplored();
    const zoneColor = {}, zoneName = {};
    const agg = new Map();
    if (atlas) {
      // the whole world, fog-dimmed where uncharted
      atlas.zones.forEach(z => { zoneColor[z.id] = z.color; zoneName[z.id] = z.name; });
      for (const r of atlas.rooms) {
        const a = agg.get(r.zone) || { sx: 0, sy: 0, n: 0, seen: 0 };
        a.sx += r.x; a.sy += r.y; a.n++;
        if (explored.has(r.vnum)) a.seen++;
        agg.set(r.zone, a);
      }
    } else {
      (payload.zones || []).forEach(z => { zoneColor[z.id] = z.color; zoneName[z.id] = z.name; });
      for (const r of (payload.rooms || [])) {
        const a = agg.get(r.zone) || { sx: 0, sy: 0, n: 0, seen: 0 };
        a.sx += r.x; a.sy += r.y; a.n++; a.seen++;
        agg.set(r.zone, a);
      }
    }
    if (!agg.size) { host.innerHTML = '<div style="color:#6a7084;padding:30px;font-family:var(--ui-font)">Explore to chart the world…</div>'; return; }
    const pts = [...agg.entries()].map(([id, a]) => ({ id, x: a.sx / a.n, y: a.sy / a.n, n: a.n, seen: a.seen }));
    // force-directed layout: geography seeds it, then springs pull linked
    // regions together while repulsion spreads the cards across the canvas
    const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const PAD = 110;
    pts.forEach((p, i) => {
      p.px = PAD + ((p.x - x0) / Math.max(1, x1 - x0)) * (rect.width - PAD * 2) + (i % 7) * 3;
      p.py = PAD * 0.5 + ((p.y - y0) / Math.max(1, y1 - y0)) * (rect.height - PAD) + (i % 5) * 3;
    });
    const links = (MH.state.atlas && MH.state.atlas.links) || [];
    const byId = Object.fromEntries(pts.map(p => [p.id, p]));
    const CW = 105, CH = 34;             // half card footprint for spacing
    for (let it = 0; it < 260; it++) {
      // repulsion: no two cards may crowd each other
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const a = pts[i], b = pts[j];
          let dx = b.px - a.px, dy = (b.py - a.py) * (CW / CH);
          let d2 = dx * dx + dy * dy;
          if (d2 < 1) { dx = (i - j); dy = 1; d2 = 2; }
          const d = Math.sqrt(d2);
          if (d < CW * 2.4) {
            const f = (CW * 2.4 - d) / d * 0.18;
            const fy = f * (CH / CW);
            a.px -= dx * f; a.py -= dy * fy;
            b.px += dx * f; b.py += dy * fy;
          }
        }
      }
      // springs: connected regions stay near each other
      for (const [za, zb] of links) {
        const a = byId[za], b = byId[zb];
        if (!a || !b) continue;
        const dx = b.px - a.px, dy = b.py - a.py;
        const d = Math.hypot(dx, dy) || 1;
        const f = (d - 230) / d * 0.012;
        a.px += dx * f; a.py += dy * f;
        b.px -= dx * f; b.py -= dy * f;
      }
      // gentle pull toward center keeps islands on the canvas
      for (const p of pts) {
        p.px += (rect.width / 2 - p.px) * 0.0035;
        p.py += (rect.height / 2 - p.py) * 0.0035;
        p.px = Math.max(PAD * 0.7, Math.min(rect.width - PAD * 0.7, p.px));
        p.py = Math.max(36, Math.min(rect.height - 36, p.py));
      }
    }
    const at = Object.fromEntries(pts.map(p => [p.id, p]));
    // roads between connected regions, beneath the cards
    if (atlas && atlas.links) {
      lctx.lineWidth = 1.5;
      for (const [za, zb] of atlas.links) {
        const a = at[za], b = at[zb];
        if (!a || !b) continue;
        const lit = a.seen > 0 && b.seen > 0;
        lctx.strokeStyle = lit ? 'rgba(232,193,104,0.45)' : 'rgba(120,128,150,0.16)';
        lctx.setLineDash(lit ? [] : [4, 5]);
        lctx.beginPath();
        lctx.moveTo(a.px, a.py);
        const mx = (a.px + b.px) / 2, my = (a.py + b.py) / 2 - 18;
        lctx.quadraticCurveTo(mx, my, b.px, b.py);
        lctx.stroke();
      }
      lctx.setLineDash([]);
    }
    const hereZone = (payload.rooms || []).find(r => r.vnum === payload.player.vnum);
    for (const p of pts) {
      const card = document.createElement('div');
      const uncharted = p.seen === 0;
      card.className = 'wm-zone-card' + (hereZone && hereZone.zone === p.id ? ' here' : '') + (uncharted ? ' fog' : '');
      card.style.setProperty('--zc', zoneColor[p.id] || '#4a4f60');
      card.style.left = Math.max(70, Math.min(rect.width - 70, p.px)) + 'px';
      card.style.top = Math.max(30, Math.min(rect.height - 30, p.py)) + 'px';
      card.innerHTML = `<div class="zn">${zoneName[p.id] || 'Uncharted'}</div><div class="zc">${p.seen}/${p.n} charted</div>`;
      card.addEventListener('click', () => {
        wmZoneId = p.id;
        const src = MH.state.atlas ? MH.state.atlas.rooms : (payload.rooms || []);
        const zs = [...new Set(src.filter(r => r.zone === p.id).map(r => r.z || 0))];
        const pz = hereZone && hereZone.zone === p.id ? (payload.player.z || 0) : null;
        wmZ = pz != null && zs.includes(pz) ? pz : zs.sort((a, b) => Math.abs(a) - Math.abs(b))[0] || 0;
        wmView = 'zone';
        wmRender();
      });
      host.appendChild(card);
    }
  }

  function wmRenderZone(payload) {
    const canvas = $('wm-zone');
    canvas.style.pointerEvents = '';
    const body = $('wm-body');
    const rect = body.getBoundingClientRect();
    canvas.width = rect.width; canvas.height = rect.height;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const atlas = MH.state.atlas;
    const explored = wmExplored();
    const zoneColor = {}, zoneName = {};
    const zsrc = atlas ? atlas.zones : (payload.zones || []);
    zsrc.forEach(z => { zoneColor[z.id] = z.color; zoneName[z.id] = z.name; });
    const src = atlas ? atlas.rooms : (payload.rooms || []);
    const all = src.filter(r => r.zone === wmZoneId);
    const zs = [...new Set(all.map(r => r.z || 0))].sort((a, b) => b - a);
    if (!zs.includes(wmZ)) wmZ = zs[0] || 0;
    const rooms = all.filter(r => (r.z || 0) === wmZ);
    $('wm-crumb').innerHTML = '<span id="wm-back" style="cursor:pointer">WORLD</span><span class="sep">›</span><span class="here">' + (zoneName[wmZoneId] || '?') + '</span>';
    const back = document.getElementById('wm-back');
    if (back) back.onclick = () => { wmView = 'world'; wmRender(); };
    $('wm-levels').innerHTML = zs.map(z =>
      `<span class="${z === wmZ ? 'on' : ''}" data-z="${z}">${z === 0 ? 'ground' : z > 0 ? '▲' + z : '▼' + (-z)}</span>`).join('');
    $('wm-levels').querySelectorAll('span').forEach(el =>
      el.addEventListener('click', () => { wmZ = Number(el.dataset.z); wmRender(); }));
    wmHit = [];
    if (!rooms.length) return;
    // percentile extents: a handful of collision-slid outliers must not
    // shrink the whole town into a corner - they clamp to the map's edge
    const q = (arr, t) => arr[Math.max(0, Math.min(arr.length - 1, Math.floor(arr.length * t)))];
    const xs = rooms.map(r => r.x).sort((a, b) => a - b);
    const ys = rooms.map(r => r.y).sort((a, b) => a - b);
    const x0 = q(xs, 0.08), x1 = Math.max(q(xs, 0.92), x0 + 1);
    const y0 = q(ys, 0.08), y1 = Math.max(q(ys, 0.92), y0 + 1);
    const PAD = 50;
    const cell = Math.max(7, Math.min(26,
      Math.min((rect.width - PAD * 2) / (x1 - x0 + 1), (rect.height - PAD * 2) / (y1 - y0 + 1))));
    const offX = (rect.width - (x1 - x0 + 1) * cell) / 2;
    const offY = (rect.height - (y1 - y0 + 1) * cell) / 2;
    const clampX = v => Math.max(14, Math.min(rect.width - 14, v));
    const clampY = v => Math.max(14, Math.min(rect.height - 14, v));
    const px = r => clampX(offX + (r.x - x0) * cell + cell / 2);
    const py = r => clampY(offY + (r.y - y0) * cell + cell / 2);
    const here = new Map(rooms.map(r => [r.vnum, r]));

    // every real connection gets a line, however far the rooms sit apart;
    // exits beyond the zone or level get a short stub with a hint
    const stubs = [];
    for (const r of rooms) {
      const ex = r.exits || {};
      const pairs = Array.isArray(ex) ? ex.map(d => [d, null]) : Object.entries(ex);
      for (const [d, tv] of pairs) {
        if (tv == null) continue;          // explored-payload fallback has no targets
        if (here.has(tv)) {
          if (tv > r.vnum) {               // draw each link once
            const nb = here.get(tv);
            const lit = explored.has(r.vnum) && explored.has(tv);
            ctx.strokeStyle = lit ? 'rgba(180,190,215,0.5)' : 'rgba(120,128,150,0.18)';
            ctx.lineWidth = Math.max(1, cell * 0.1);
            ctx.beginPath(); ctx.moveTo(px(r), py(r)); ctx.lineTo(px(nb), py(nb)); ctx.stroke();
          }
        } else if (atlas) {
          const target = atlas.byVnum.get(tv);
          if (!target) continue;
          if (target.zone === wmZoneId) continue;   // other level of same zone: the ▲▼ dot covers it
          stubs.push({ r, d, zone: zoneName[target.zone] || '?' });
        }
      }
    }
    // cross-zone gateways: a stub arrow + the destination's name
    const DIRV2 = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0], up: [0.6, -0.6], down: [-0.6, 0.6] };
    ctx.font = '10px Trebuchet MS, Verdana, sans-serif';
    for (const sb of stubs) {
      const o = DIRV2[sb.d] || [0.6, -0.6];
      const X = px(sb.r), Y = py(sb.r);
      const ex2 = X + o[0] * cell * 1.6, ey2 = Y + o[1] * cell * 1.6;
      const lit = explored.has(sb.r.vnum);
      ctx.strokeStyle = lit ? 'rgba(232,193,104,0.8)' : 'rgba(150,140,110,0.3)';
      ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(X, Y); ctx.lineTo(ex2, ey2); ctx.stroke();
      ctx.fillStyle = lit ? 'rgba(232,193,104,0.9)' : 'rgba(150,140,110,0.4)';
      ctx.beginPath(); ctx.arc(ex2, ey2, 2.2, 0, 7); ctx.fill();
      if (lit) ctx.fillText('→ ' + sb.zone, ex2 + 4, ey2 + 3);
    }
    // rooms: bright when charted, fog-ghosts when not
    const color = zoneColor[wmZoneId] || '#4a4f60';
    for (const r of rooms) {
      const X = px(r), Y = py(r);
      const lit = explored.has(r.vnum);
      if (lit) {
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.9;
        ctx.fillRect(X - cell * 0.38, Y - cell * 0.38, cell * 0.76, cell * 0.76);
        ctx.globalAlpha = 1;
      } else {
        ctx.strokeStyle = 'rgba(140,150,180,0.28)';
        ctx.lineWidth = 1;
        ctx.strokeRect(X - cell * 0.3, Y - cell * 0.3, cell * 0.6, cell * 0.6);
      }
      const ex = r.exits || {};
      const dirs = Array.isArray(ex) ? ex : Object.keys(ex);
      if (dirs.includes('up') || dirs.includes('down')) {
        ctx.fillStyle = lit ? '#e8e2d0' : 'rgba(180,180,170,0.35)';
        ctx.fillRect(X - 1, Y - 1, 2, 2);
      }
      wmHit.push({ x: X, y: Y, vnum: r.vnum, name: r.name, lit });
    }
    const me = rooms.find(r => r.vnum === payload.player.vnum);
    if (me) {
      const X = px(me), Y = py(me);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.strokeRect(X - cell * 0.5, Y - cell * 0.5, cell, cell);
      ctx.fillStyle = '#ffe9a8';
      ctx.beginPath(); ctx.arc(X, Y, Math.max(2.5, cell * 0.16), 0, 7); ctx.fill();
    }
  }

  function wmNearest(e) {
    const rect = $('wm-zone').getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    let best = null, bd = 14;
    for (const h of wmHit) {
      const d = Math.hypot(h.x - mx, h.y - my);
      if (d < bd) { bd = d; best = h; }
    }
    return best;
  }

  // the map column lives in the black letterbox band right of the play
  // area - never over the world. Sized to whatever band the window gives.
  function fitMinimapColumn() {
    const wrap = document.getElementById('minimap-wrap');
    if (!wrap || !els.minimap) return;
    let band = 220;
    try {
      const sc = MH.game.scene.getScenes(true).find(s2 => s2.buildRoom);
      const cam = sc.cameras.main;
      const gc = sc.game.canvas.getBoundingClientRect();
      const roomRight = gc.left + (sc.pxW - cam.worldView.x) * cam.zoom;
      band = window.innerWidth - roomRight;
    } catch (_) { /* scene not up yet */ }
    const w = Math.round(Math.max(150, Math.min(300, band - 26)));
    els.minimap.width = mmLarge ? Math.max(w, 300) : w;
    els.minimap.height = mmLarge ? 520 : 340;
    renderMinimap();
  }
  MH.fitMinimapColumn = fitMinimapColumn;

  function toggleMinimapSize() {
    mmLarge = !mmLarge;
    fitMinimapColumn();
  }

  // ---- compass: click an exit to auto-run there and take it ----
  const CARDINAL_SET = ['north', 'south', 'east', 'west', 'up', 'down'];
  function renderCompass() {
    const exits = (MH.state.currentRoom && MH.state.currentRoom.exits) || {};
    const cell = (label, dir) => {
      const has = dir && Object.prototype.hasOwnProperty.call(exits, dir);
      const zone = has && exits[dir].to_zone;
      const cls = dir == null ? 'cmp spacer' : `cmp${has ? ' on' : ''}${zone ? ' zone' : ''}`;
      const title = zone ? ` title="→ ${zone}"` : '';
      return `<div class="${cls}" ${has ? `data-dir="${dir}"` : ''}${title}>${label}</div>`;
    };
    let html = '';
    html += cell('', null) + cell('N', 'north') + cell('', null) + cell('U', 'up');
    html += cell('W', 'west') + cell('·', null) + cell('E', 'east') + cell('D', 'down');
    html += cell('', null) + cell('S', 'south') + cell('', null) + cell('', null);
    for (const name of Object.keys(exits)) {
      if (CARDINAL_SET.includes(name)) continue;
      html += `<div class="cmp on portal" data-dir="${name}">⟡ ${name}</div>`;
    }
    els.compass.innerHTML = html;
    els.compass.querySelectorAll('.cmp.on').forEach(el =>
      el.addEventListener('click', () => MH.bus.emit('nav.goto', el.dataset.dir)));
  }

  // ---- talent trees (WoW-style specs; data straight from the MUD) ----
  function talentsUrl() {
    const name = encodeURIComponent(MH.state.playerName);
    const host = window.location.hostname || 'localhost';
    const isProxy = !window.location.port || window.location.port == 80 || window.location.port == 443;
    return isProxy ? `/talents?player=${name}` : `${window.location.protocol}//${host}:4001/talents?player=${name}`;
  }

  // ---- talents as constellations: stars, prereq lines, a trinity of trees ----
  const TREE_HUES = ['#ff9a5a', '#7ab8ff', '#c08aff'];
  let constAnim = null;

  function specTitle(data) {
    const total = data.trees.reduce((a, t) => a + t.points, 0);
    if (!total) return { txt: 'An Unwritten Star', pct: 0, idx: -1 };
    let best = 0;
    data.trees.forEach((t, i) => { if (t.points > data.trees[best].points) best = i; });
    const pct = Math.round((data.trees[best].points / total) * 100);
    const name = data.trees[best].name;
    const rank = pct >= 80 ? 'Avatar of' : pct >= 60 ? 'Master of' : pct >= 40 ? 'Disciple of' : 'Student of';
    return { txt: `${rank} ${name} · ${pct}%`, pct, idx: best };
  }

  function layoutConstellation(data, W) {
    const colW = W / data.trees.length;
    const nodes = [];
    data.trees.forEach((tree, ti) => {
      const tiers = {};
      tree.talents.forEach(t => { (tiers[t.tier] = tiers[t.tier] || []).push(t); });
      const tierKeys = Object.keys(tiers).map(Number).sort((a, b) => a - b);
      tierKeys.forEach((tier, row) => {
        const list = tiers[tier];
        list.forEach((t, i) => {
          const jx = ((MH.hashStr(t.id) % 17) - 8) * 1.6;
          const jy = ((MH.hashStr(t.id + 'y') % 11) - 5) * 1.5;
          nodes.push({
            t, ti, tree,
            x: ti * colW + colW * ((i + 1) / (list.length + 1)) + jx,
            y: 46 + row * 52 + jy,
          });
        });
      });
    });
    return nodes;
  }

  function drawConstellation(cv, data, nodes, phase, hover) {
    const x = cv.getContext('2d');
    const W = cv.width, H = cv.height;
    x.clearRect(0, 0, W, H);
    // night sky
    const bg = x.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#0b0d18'); bg.addColorStop(1, '#11142a');
    x.fillStyle = bg; x.fillRect(0, 0, W, H);
    for (let i = 0; i < 70; i++) {
      const sx = (MH.hashStr('bg' + i) % W), sy = (MH.hashStr('bgy' + i) % H);
      x.globalAlpha = 0.12 + 0.1 * Math.sin(phase / 700 + i);
      x.fillStyle = '#cfd8ff';
      x.fillRect(sx, sy, 1.4, 1.4);
    }
    x.globalAlpha = 1;
    const colW = W / data.trees.length;
    const byId = Object.fromEntries(nodes.map(n => [n.t.id, n]));
    // tree headers + column separators + milestone runes
    data.trees.forEach((tree, ti) => {
      const hue = TREE_HUES[ti % 3];
      if (ti) { x.strokeStyle = 'rgba(140,150,180,0.12)'; x.beginPath(); x.moveTo(ti * colW, 14); x.lineTo(ti * colW, H - 8); x.stroke(); }
      x.font = '600 12px Trebuchet MS, Verdana, sans-serif';
      x.fillStyle = hue;
      x.textAlign = 'center';
      x.fillText(`${tree.icon || '✦'} ${tree.name}`, ti * colW + colW / 2, 18);
      x.font = '9px Trebuchet MS, Verdana, sans-serif';
      x.fillStyle = '#8a90a4';
      x.fillText(`${tree.points} pts`, ti * colW + colW / 2, 30);
      // milestone runes: 5/15/25 -> identity passive
      [5, 15, 25].forEach((ms, mi) => {
        const mx = ti * colW + colW / 2 + (mi - 1) * 26;
        const lit = tree.points >= ms;
        x.globalAlpha = lit ? 0.95 : 0.25;
        x.fillStyle = lit ? hue : '#6a7084';
        x.beginPath();
        x.moveTo(mx, H - 16); x.lineTo(mx + 4, H - 10); x.lineTo(mx, H - 4); x.lineTo(mx - 4, H - 10);
        x.closePath(); x.fill();
        if (lit && ms === 25) { x.globalAlpha = 0.35 + 0.25 * Math.sin(phase / 300); x.beginPath(); x.arc(mx, H - 10, 9, 0, 7); x.strokeStyle = hue; x.stroke(); }
      });
      x.globalAlpha = 1;
    });
    x.textAlign = 'left';
    // prereq starlines
    for (const n of nodes) {
      for (const req of (n.t.requires || [])) {
        const from = byId[req];
        if (!from) continue;
        const lit = from.t.rank > 0;
        x.strokeStyle = lit ? TREE_HUES[n.ti % 3] : 'rgba(140,150,180,0.18)';
        x.globalAlpha = lit ? 0.5 : 1;
        x.lineWidth = lit ? 1.4 : 1;
        x.beginPath(); x.moveTo(from.x, from.y); x.lineTo(n.x, n.y); x.stroke();
        x.globalAlpha = 1;
      }
    }
    // stars
    for (const n of nodes) {
      const hue = TREE_HUES[n.ti % 3];
      const st = n.state;
      const r = 4 + n.t.rank * 1.1 + (st === 'maxed' ? 2 : 0);
      if (st === 'maxed' || st === 'ranked') {
        const g = x.createRadialGradient(n.x, n.y, 1, n.x, n.y, r * 3.4);
        g.addColorStop(0, hue + 'cc'); g.addColorStop(1, hue + '00');
        x.fillStyle = g; x.beginPath(); x.arc(n.x, n.y, r * 3.4, 0, 7); x.fill();
      }
      if (st === 'learnable') {
        const pr = 7 + 2.4 * Math.sin(phase / 260 + n.x);
        x.strokeStyle = '#ffe9a8';
        x.globalAlpha = 0.75;
        x.beginPath(); x.arc(n.x, n.y, pr, 0, 7); x.stroke();
        x.globalAlpha = 1;
      }
      x.fillStyle = st === 'locked' ? '#3c4254' : st === 'learnable' ? '#e8e2d0' : hue;
      x.beginPath(); x.arc(n.x, n.y, Math.max(3, r), 0, 7); x.fill();
      if (st === 'maxed') {
        x.strokeStyle = '#ffe9a8'; x.lineWidth = 1.2;
        x.beginPath(); x.arc(n.x, n.y, r + 3, 0, 7); x.stroke();
      }
      if (hover === n) {
        x.strokeStyle = '#ffffff'; x.lineWidth = 1;
        x.beginPath(); x.arc(n.x, n.y, r + 5, 0, 7); x.stroke();
      }
    }
  }

  function drawTrinity(cv, data, phase) {
    const x = cv.getContext('2d');
    const W = cv.width, H = cv.height;
    x.clearRect(0, 0, W, H);
    const cx = W / 2, cy = H / 2 + 8, R = H / 2 - 22;
    const corners = data.trees.map((t, i) => {
      const a = -Math.PI / 2 + i * (Math.PI * 2 / 3);
      return { x: cx + Math.cos(a) * R, y: cy + Math.sin(a) * R, t, hue: TREE_HUES[i % 3] };
    });
    // triangle frame
    x.strokeStyle = 'rgba(232,193,104,0.35)';
    x.lineWidth = 1.2;
    x.beginPath();
    corners.forEach((c, i) => i ? x.lineTo(c.x, c.y) : x.moveTo(c.x, c.y));
    x.closePath(); x.stroke();
    // corner crests
    x.textAlign = 'center';
    corners.forEach(c => {
      const g = x.createRadialGradient(c.x, c.y, 1, c.x, c.y, 16);
      g.addColorStop(0, c.hue + '88'); g.addColorStop(1, c.hue + '00');
      x.fillStyle = g; x.beginPath(); x.arc(c.x, c.y, 16, 0, 7); x.fill();
      x.font = '12px Trebuchet MS, Verdana, sans-serif';
      x.fillStyle = c.hue;
      const above = c.y < cy;
      x.fillText(`${c.t.icon || '✦'} ${c.t.name} · ${c.t.points}`, c.x, c.y + (above ? -22 : 30));
    });
    // your build: a star pulled toward where the points lean
    const total = data.trees.reduce((a, t) => a + t.points, 0);
    let bx = cx, by = cy;
    if (total > 0) {
      bx = corners.reduce((a, c) => a + c.x * (c.t.points / total), 0);
      by = corners.reduce((a, c) => a + c.y * (c.t.points / total), 0);
    }
    const spec = data.titleOverride || specTitle(data);
    const hue = spec.idx >= 0 ? TREE_HUES[spec.idx % 3] : '#e8c168';
    const g2 = x.createRadialGradient(bx, by, 1, bx, by, 18 + 4 * Math.sin(phase / 320));
    g2.addColorStop(0, hue + 'ee'); g2.addColorStop(1, hue + '00');
    x.fillStyle = g2; x.beginPath(); x.arc(bx, by, 22, 0, 7); x.fill();
    x.fillStyle = '#fff';
    x.beginPath();
    for (let i = 0; i < 5; i++) {
      const a = -Math.PI / 2 + i * Math.PI * 4 / 5;
      const px2 = bx + Math.cos(a) * 6, py2 = by + Math.sin(a) * 6;
      i ? x.lineTo(px2, py2) : x.moveTo(px2, py2);
    }
    x.closePath(); x.fill();
    x.font = '600 12.5px Georgia, serif';
    x.fillStyle = '#e8e2d0';
    x.fillText(spec.txt, cx, H - 4);
    x.textAlign = 'left';
  }

  async function renderTalents() {
    els.talentsBody.innerHTML = '<div class="slot">consulting the trainers…</div>';
    let data;
    try {
      const res = await fetch(talentsUrl());
      data = await res.json();
    } catch (_) {
      els.talentsBody.innerHTML = '<div class="slot">talent data unavailable</div>';
      return;
    }
    if (!data.has_trees) {
      renderDoctrine();
      return;
    }
    const W = 508;
    const maxTiers = Math.max(...data.trees.map(t => Math.max(...t.talents.map(a => a.tier))));
    const CH = 60 + maxTiers * 52;
    // constellation first - it's the hero; trinity + path cards live below
    els.talentsBody.innerHTML =
      `<div class="talent-points">★ ${data.points_available} talent point${data.points_available === 1 ? '' : 's'} to place`
      + ` <span style="color:#7a8094">(${data.points_total} earned by leveling · click a pulsing star)</span></div>`
      + `<canvas id="const-cv" width="${W}" height="${CH}" class="skyframe"></canvas>`
      + `<canvas id="trinity-cv" width="${W}" height="170" class="skyframe" style="margin-top:8px"></canvas>`
      + pathCardsHtml()
      + `<div id="tal-tip"></div>`;
    wirePathButtons(els.talentsBody);

    const cv = document.getElementById('const-cv');
    const tcv = document.getElementById('trinity-cv');
    const tip = document.getElementById('tal-tip');
    const nodes = layoutConstellation(data, W);
    const allT = data.trees.flatMap(tr => tr.talents);
    const tierNeed = tier => (tier - 1) * 5;
    for (const n of nodes) {
      const t = n.t;
      const prereqMet = (t.requires || []).every(r => { const pre = allT.find(a2 => a2.id === r); return pre && pre.rank > 0; });
      const tierOpen = n.tree.points >= tierNeed(t.tier);
      n.state = t.rank >= t.max_rank ? 'maxed'
        : (tierOpen && prereqMet && data.points_available > 0) ? (t.rank > 0 ? 'ranked' : 'learnable')
        : t.rank > 0 ? 'ranked' : 'locked';
      if (n.state === 'ranked' && tierOpen && prereqMet && data.points_available > 0) n.clickable = true;
      if (n.state === 'learnable') n.clickable = true;
    }
    let hover = null;
    const loop = ts => {
      if (!document.body.contains(cv)) { constAnim = null; return; }
      drawConstellation(cv, data, nodes, ts, hover);
      drawTrinity(tcv, data, ts);
      constAnim = requestAnimationFrame(loop);
    };
    if (constAnim) cancelAnimationFrame(constAnim);
    constAnim = requestAnimationFrame(loop);

    const nodeAt = e => {
      const r = cv.getBoundingClientRect();
      const mx = (e.clientX - r.left) * (cv.width / r.width);
      const my = (e.clientY - r.top) * (cv.height / r.height);
      let best = null, bd = 16;
      for (const n of nodes) { const d = Math.hypot(n.x - mx, n.y - my); if (d < bd) { bd = d; best = n; } }
      return best;
    };
    cv.addEventListener('mousemove', e => {
      hover = nodeAt(e);
      cv.style.cursor = hover && hover.clickable ? 'pointer' : 'default';
      if (hover) {
        const t = hover.t;
        const req = (t.requires || []).length ? `<div class="tt-req">requires: ${t.requires.map(r => (allT.find(a2 => a2.id === r) || { name: r }).name).join(', ')}</div>` : '';
        const gate = hover.tree.points < tierNeed(t.tier) ? `<div class="tt-req">tier opens at ${tierNeed(t.tier)} points in ${hover.tree.name}</div>` : '';
        tip.innerHTML = `<b style="color:${TREE_HUES[hover.ti % 3]}">${t.name}</b> <span class="tt-rank">${t.rank}/${t.max_rank}</span>`
          + `<div class="tt-desc">${t.description}</div>${req}${gate}`
          + (hover.clickable ? '<div class="tt-go">✦ click to learn</div>' : '');
        tip.style.display = 'block';
        const rr = cv.getBoundingClientRect();
        tip.style.left = Math.min(e.clientX - rr.left + 14, rr.width - 230) + 'px';
        tip.style.top = (e.clientY - rr.top + cv.offsetTop - 10) + 'px';
      } else tip.style.display = 'none';
    });
    cv.addEventListener('mouseleave', () => { hover = null; tip.style.display = 'none'; });
    cv.addEventListener('click', e => {
      const n = nodeAt(e);
      if (!n || !n.clickable) return;
      MH.sendCommand(`talents learn ${n.t.id}`);
      // starburst on the spot
      const r = cv.getBoundingClientRect();
      flash(`✦ ${n.t.name}`);
      setTimeout(() => { renderTalents(); MH.refreshState(); }, 650);
    });
  }

  function pathCardsHtml() {
    const pp = MH.state.player || {};
    return `<div class="doctrine-cards" style="grid-template-columns:1fr 1fr; margin-bottom:10px">`
      + `<div class="dcard${pp.path === 'lone_wolf' ? ' sworn' : ''}"><div class="dname">🐺 Lone Wolf${pp.path === 'lone_wolf' ? ' ★' : ''}</div>`
      + `<div class="ddesc">Ungrouped: damage reduction, lifesteal, consumable mastery. Solo anything - with strategy and a full satchel.</div>`
      + (pp.path !== 'lone_wolf' ? `<button data-path="lone_wolf">WALK IT</button>` : '') + `</div>`
      + `<div class="dcard${pp.path === 'fellowship' ? ' sworn' : ''}"><div class="dname">🤝 Fellowship${pp.path === 'fellowship' ? ' ★' : ''}</div>`
      + `<div class="ddesc">Grouped: +15% experience and coordinated strikes on shared targets. Alone, nothing.</div>`
      + (pp.path !== 'fellowship' ? `<button data-path="fellowship">WALK IT</button>` : '') + `</div></div>`
      + `<div class="slot" style="margin-bottom:10px">First choice is free · switching (and talent respec) requires the Trial of Unlearning - Sage Aldric, Temple of Midgaard</div>`;
  }
  function wirePathButtons(container) {
    container.querySelectorAll('[data-path]').forEach(btn =>
      btn.addEventListener('click', () => {
        commandWithPeek(`path ${btn.dataset.path}`);
        setTimeout(() => { MH.refreshState(); showSpellsTab('talents'); }, 1000);
      }));
  }

  // warriors: doctrines + ability evolution instead of trees
  async function renderDoctrine() {
    let d;
    try {
      const url = talentsUrl().replace('/talents', '/doctrine');
      d = await (await fetch(url)).json();
    } catch (_) {
      els.talentsBody.innerHTML = '<div class="slot">doctrine data unavailable</div>';
      return;
    }
    // oath trinity leads; path cards move to the bottom of the panel
    let html = `<canvas id="doctrine-cv" width="508" height="160" class="skyframe" style="margin-bottom:8px"></canvas>`;
    html += `<div class="talent-points">⚔ MARTIAL DOCTRINES`
      + (d.doctrine ? ` <span style="color:#aab2c4">· sworn to the <b>${d.doctrine.replace(/_/g, ' ')}</b> · momentum ${d.momentum}</span>`
                    : ' <span style="color:#aab2c4">· swear to one path - the choice shapes every ability</span>')
      + `</div><div class="doctrine-cards">`;
    for (const [id, doc] of Object.entries(d.doctrines)) {
      const sworn = d.doctrine === id;
      html += `<div class="dcard${sworn ? ' sworn' : ''}">`
        + `<div class="dname">${doc.name}${sworn ? ' ★' : ''}</div>`
        + `<div class="ddesc">${doc.description}</div>`
        + `<div class="dflavor">${doc.flavor}</div>`
        + (doc.bonus ? `<div class="dbonus">${doc.bonus}</div>` : '')
        + (!d.doctrine ? `<button data-swear="${id}">SWEAR</button>` : '')
        + `</div>`;
    }
    html += '</div>';
    // evolution tracks: every ability grows with use
    html += '<div class="talent-points" style="font-size:13px">ABILITY EVOLUTION <span style="color:#aab2c4">· abilities transform through use</span></div>';
    for (const ab of d.abilities) {
      const ths = Object.keys(ab.thresholds).map(Number).sort((a, b) => a - b);
      const next = ths.find(t => ab.usage < t);
      const maxTh = ths[ths.length - 1] || 1;
      const frac = Math.min(1, ab.usage / maxTh);
      html += `<div class="evo-card"><div class="ehead">`
        + `<span class="ename">${ab.ability}${ab.evolved ? ` → ${ab.evolved.replace(/_/g, ' ')}` : ''}</span>`
        + `<span class="eusage">${ab.usage} uses${next ? ` · next at ${next}` : ' · fully evolved path'}</span></div>`
        + `<div class="evo-track"><i style="width:${frac * 100}%"></i></div>`;
      for (const th of ths) {
        const reached = ab.usage >= th;
        const paths = ab.thresholds[String(th)];
        const mine = d.doctrine && paths[d.doctrine];
        if (mine) {
          const [evoId, desc] = mine;
          const done = ab.evolved === evoId;
          const cls = done ? 'evo-step done' : reached ? 'evo-step ready' : 'evo-step';
          html += `<div class="${cls}">${th} uses → <b>${evoId.replace(/_/g, ' ')}</b>: ${desc}`
            + (reached && !done && !ab.evolved ? ` <button data-evolve="${ab.ability}">EVOLVE</button>` : (done ? ' ✓' : ''))
            + `</div>`;
        } else if (!d.doctrine) {
          html += `<div class="evo-step">${th} uses → <span style="color:#8a90a4">${Object.values(paths).map(p2 => p2[0].replace(/_/g, ' ')).join(' / ')} (per doctrine)</span></div>`;
        }
      }
      html += '</div>';
    }
    html += pathCardsHtml();
    els.talentsBody.innerHTML = html;
    const dcv = document.getElementById('doctrine-cv');
    if (dcv) {
      const docs = Object.entries(d.doctrines).slice(0, 3);
      const totalUse = (d.abilities || []).reduce((a, ab) => a + (ab.usage || 0), 0);
      const synth = {
        trees: docs.map(([id, doc]) => ({
          name: doc.name.replace(/ Doctrine.*/i, ''),
          icon: '⚔',
          points: d.doctrine === id ? Math.max(1, totalUse) : 0,
        })),
        titleOverride: d.doctrine
          ? { txt: `Sworn to the ${(d.doctrines[d.doctrine] || {}).name || d.doctrine} · ${totalUse} deeds`, idx: docs.findIndex(([id]) => id === d.doctrine) }
          : { txt: 'Unsworn — three oaths await', idx: -1 },
      };
      const loop2 = ts => {
        if (!document.body.contains(dcv)) return;
        drawTrinity(dcv, synth, ts);
        requestAnimationFrame(loop2);
      };
      requestAnimationFrame(loop2);
    }
    wirePathButtons(els.talentsBody);
    els.talentsBody.querySelectorAll('[data-swear]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.swear;
        if (!window.confirm(`Swear to the ${id.replace(/_/g, ' ')}? Doctrines shape your warrior permanently.`)) return;
        MH.sendCommand(`swear ${id}`);
        // the MUD asks for confirmation; give it
        setTimeout(() => MH.sendCommand(`swear ${id}`, false), 700);
        setTimeout(renderDoctrine, 1800);
      });
    });
    els.talentsBody.querySelectorAll('[data-evolve]').forEach(btn => {
      btn.addEventListener('click', () => {
        MH.sendCommand(`evolve ${btn.dataset.evolve}`);
        setTimeout(renderDoctrine, 1200);
      });
    });
  }

  function showSpellsTab(which) {
    els.spellsBody.style.display = which === 'abilities' ? '' : 'none';
    els.talentsBody.style.display = which === 'talents' ? '' : 'none';
    document.querySelectorAll('.mtab').forEach(t => t.classList.toggle('active', t.dataset.mtab === which));
    if (which === 'talents') renderTalents();
  }

  // ---- mob hover tooltip with a consider verdict ----
  function considerVerdict(mobLevel) {
    const p = MH.state.player;
    if (!p || mobLevel == null) return '';
    const diff = mobLevel - (p.level || 1);
    if (diff <= -10) return 'Now where did that chicken go?';
    if (diff <= -5) return 'You could do it with a needle!';
    if (diff <= -2) return 'Easy.';
    if (diff <= 1) return 'The perfect match!';
    if (diff <= 4) return 'You would need some luck!';
    if (diff <= 9) return 'You ARE mad!';
    return "Why don't you just lie down and pretend you're dead?";
  }
  function showMobTip({ data, kind, x, y }) {
    const tip = els.mobTip;
    const hp = data.hp != null && data.maxHp ? ` · ${data.hp}/${data.maxHp} hp` : '';
    const role = data.shopkeeper ? 'shopkeeper' : data.boss ? 'BOSS' : data.hostile ? 'hostile' : (kind === 'player' ? (data.char_class || 'adventurer') : 'neutral');
    const verdict = kind === 'mob' && !data.shopkeeper ? `<div class="verdict">"${considerVerdict(data.level)}"</div>` : '';
    tip.innerHTML = `<div class="nm">${data.name}</div><div class="meta">level ${data.level ?? '?'} · ${role}${hp}</div>${verdict}`;
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect();
    tip.style.left = `${Math.min(window.innerWidth - r.width - 8, x + 14)}px`;
    tip.style.top = `${Math.max(8, y - r.height - 10)}px`;
  }
  function hideMobTip() { els.mobTip.style.display = 'none'; }

  // ---- low-HP vignette ----
  function updateVignette() {
    const p = MH.state.player;
    if (!p || !els.vignette) return;
    const frac = (p.max_hp || 1) > 0 ? (p.hp || 0) / (p.max_hp || 1) : 1;
    if (frac < 0.4) {
      els.vignette.style.opacity = String(Math.min(0.95, ((0.4 - frac) / 0.4) * 1.1));
      els.vignette.classList.toggle('pulse', frac < 0.2);
    } else {
      els.vignette.style.opacity = '0';
      els.vignette.classList.remove('pulse');
    }
  }

  // ---- NPC dialogue: talk on click, accept quests with buttons ----
  async function openDialogue({ name, quest }) {
    openModal('modal-dialogue');
    $('dialogue-title').textContent = name.toUpperCase();
    els.dialogueBody.innerHTML = '<div class="slot">…</div>';
    const kw = MH.mobKeyword(name);
    const p1 = captureOutput(1300);
    MH.sendCommand(`talk ${kw}`, false);
    const talkLines = await p1;
    let html = '';
    const said = talkLines.filter(l => l.trim() && !/^\d+\/\d+hp/.test(l) && !/^>/.test(l) && !/quest accept/i.test(l));
    if (said.length) html += `<div style="font-style:italic;color:#d8d2bc">${said.slice(0, 10).join('<br>')}</div>`;
    if (quest) {
      // ask the server what they're offering
      const p2 = captureOutput(1300);
      MH.sendCommand('quest', false);
      const qLines = await p2;
      const offers = [];
      talkLines.concat(qLines).forEach(l => {
        const m = l.match(/quest accept (\S+)/i);
        const id = m && m[1].replace(/\)$/, '');
        if (id && /^[a-z0-9_]+$/i.test(id) && !offers.includes(id)) offers.push(id);
      });
      const qText = qLines.filter(l => l.trim() && !/^\d+\/\d+hp/.test(l) && !/quest accept/i.test(l) && !/^>/.test(l)).slice(0, 14);
      if (qText.length) html += `<div style="margin-top:10px;color:#c2c8d6">${qText.join('<br>')}</div>`;
      if (offers.length) {
        html += '<div style="margin-top:8px">'
          + offers.map(id => `<span class="quest-btn" data-q="${id}">✦ ACCEPT: ${id.replace(/_/g, ' ')}</span>`).join('')
          + '</div>';
      } else if (quest === '?') {
        html += `<div style="margin-top:8px"><span class="quest-btn" data-turnin="1">✔ TURN IN QUEST</span></div>`;
      }
    }
    els.dialogueBody.innerHTML = html || '<div class="slot">They have nothing to say.</div>';
    els.dialogueBody.querySelectorAll('[data-q]').forEach(btn =>
      btn.addEventListener('click', () => {
        commandWithPeek(`quest accept ${btn.dataset.q}`);
        closeModals();
        setTimeout(() => MH.refreshState(), 800);
      }));
    els.dialogueBody.querySelectorAll('[data-turnin]').forEach(btn =>
      btn.addEventListener('click', () => {
        commandWithPeek('quest complete');
        closeModals();
        setTimeout(() => MH.refreshState(), 800);
      }));
  }

  // ---- typing focus management ----
  function setTyping(on) { MH.bus.emit('ui.typing', on); }

  // ---- init ----
  MH.ui = {
    init() {
      Object.assign(els, {
        loginOverlay: $('login-overlay'), loginName: $('login-name'), loginPass: $('login-pass'),
        loginBtn: $('login-btn'), createBtn: $('create-btn'), loginStatus: $('login-status'),
        roomName: $('room-name'), roomZone: $('room-zone'), roomDesc: $('room-desc'), flashLine: $('flash-line'),
        hudName: $('hud-name'), barHp: $('bar-hp'), txtHp: $('txt-hp'), barMana: $('bar-mana'), txtMana: $('txt-mana'),
        barMove: $('bar-move'), txtMove: $('txt-move'), hudLevel: $('hud-level'), hudGold: $('hud-gold'),
        barXp: $('bar-xp'), hudXpTxt: $('hud-xp-txt'),
        targetFrame: $('target-frame'), targetName: $('target-name'), targetHp: $('target-hp'), targetHpTxt: $('target-hp-txt'),
        hotbar: $('hotbar'), commandInput: $('command-input'),
        drawer: $('drawer'), drawerLog: $('drawer-log'), drawerTab: $('drawer-tab'),
        chatLog: $('chat-log'), chatPanel: $('chat-panel'), chatBody: $('chat-body'),
        chatInput: $('chat-input'), chatMode: $('chat-mode'),
        invBody: $('inv-body'), journalBody: $('journal-body'), shopBody: $('shop-body'), spellsBody: $('spells-body'),
        talentsBody: $('talents-body'), dialogueBody: $('dialogue-body'), createConsole: $('create-console'),
        minimap: $('minimap'), mmToggle: $('mm-toggle'), vignette: $('vignette'), mobTip: $('mob-tip'),
        compass: $('compass'), hitFlash: $('hit-flash'), combatChip: $('combat-chip'),
        combatLog: $('combat-log'), combatLogLines: $('combat-log-lines'),
        castBar: $('cast-bar'), roundBar: $('round-bar'), lootToast: $('loot-toast'), lootLines: $('loot-lines'),
        stanceBar: $('stance-bar'), momentumChip: $('momentum-chip'), finisherChip: $('finisher-chip'),
        pathChip: $('path-chip'),
        targetHpGhost: $('target-hp-ghost'),
        partyBar: $('party-bar'), partyMenu: $('party-menu'),
        almanacBody: $('almanac-body'), servicesBody: $('services-body'), stableBody: $('stable-body'),
        legendBody: $('legend-body'), questTracker: $('quest-tracker'),
        welcomeOverlay: $('welcome-overlay'), welcomeBody: $('welcome-body'), welcomeGo: $('welcome-go'),
      });

      // login
      const savedName = lsGet(NAME_KEY), savedPw = lsGet(PW_KEY);
      if (savedName) els.loginName.value = savedName;
      if (savedPw) { try { els.loginPass.value = atob(savedPw); } catch (_) {} }
      const begin = create => {
        const name = els.loginName.value.trim(), pass = els.loginPass.value;
        if (!name || !pass) { els.loginStatus.textContent = 'Need both name and password.'; els.loginStatus.className = 'error'; return; }
        if (create) {
          // creation is a conversation: show it and let them answer
          els.createConsole.style.display = 'block';
          els.loginStatus.textContent = 'Answer the questions below (type in the name box and press Enter).';
          els.loginName.value = '';
          els.loginName.placeholder = 'type answers here…';
          creationMode = true;
        }
        MH.connect(name, pass, create);
      };
      let creationMode = false;
      MH.bus.on('terminal.output', ({ text }) => {
        if (!creationMode || MH.state.isLoggedIn) return;
        const clean = text.split('\n').filter(l => l.trim()).slice(-30).join('\n');
        if (!clean) return;
        const div = document.createElement('div');
        div.textContent = clean;
        els.createConsole.appendChild(div);
        while (els.createConsole.children.length > 40) els.createConsole.removeChild(els.createConsole.firstChild);
        els.createConsole.scrollTop = els.createConsole.scrollHeight;
      });
      els.loginName.addEventListener('keydown', e => {
        if (e.key === 'Enter' && creationMode && !MH.state.isLoggedIn) {
          const v = els.loginName.value.trim();
          const sock = MH.state.mudSocket;
          if (sock && sock.readyState === WebSocket.OPEN) sock.send(v);
          els.loginName.value = '';
          e.preventDefault();
        }
      });
      MH.bus.on('login.success', () => { creationMode = false; els.createConsole.style.display = 'none'; });
      els.loginBtn.addEventListener('click', () => begin(false));
      els.createBtn.addEventListener('click', () => begin(true));
      els.loginPass.addEventListener('keydown', e => { if (e.key === 'Enter') begin(false); });

      MH.bus.on('login.status', msg => { els.loginStatus.textContent = msg; els.loginStatus.className = ''; });
      MH.bus.on('login.error', msg => { els.loginStatus.textContent = msg; els.loginStatus.className = 'error'; });
      MH.bus.on('login.success', () => {
        els.loginOverlay.classList.add('hidden');
        lsSet(NAME_KEY, MH.state.playerName);
        lsSet(PW_KEY, btoa(MH.state.playerPassword));
      });

      // terminal
      MH.bus.on('terminal.output', ({ html, text }) => {
        appendTerminal(html);
        if (capture) {
          for (const line of text.split('\n')) if (line.trim()) capture.lines.push(line);
          if (capture.bump) capture.bump();
        }
      });
      MH.bus.on('terminal.echo', cmd => appendTerminal(`> ${cmd}`, 'cmd'));
      els.drawerTab.addEventListener('click', () => els.drawer.classList.toggle('open'));

      // achievement / daily / title toasts pulled from the raw feed
      let lastAch = 0;
      MH.bus.on('terminal.output', ({ text }) => {
        if (!text) return;
        if (/ACHIEVEMENT UNLOCKED/.test(text) && Date.now() - lastAch > 1500) {
          lastAch = Date.now();
          const lines = text.split('\n').map(l => l.replace(/\x1b\[[0-9;]*m/g, '').trim()).filter(Boolean);
          const i = lines.findIndex(l => /ACHIEVEMENT UNLOCKED/.test(l));
          const name = i >= 0 && lines[i + 1] ? lines[i + 1] : 'New achievement';
          toast(`🏆 Achievement Unlocked`, name, 'ach');
          try { tone({ f: 660, f2: 990, type: 'sine', dur: 0.22, vol: 0.07 }); } catch (_) {}
        }
        if (/New title unlocked:/.test(text)) {
          const m = text.replace(/\x1b\[[0-9;]*m/g, '').match(/New title unlocked: '([^']+)'/);
          if (m) toast('🏷 Title Unlocked', m[1], 'ach');
        }
        detectWorldEvent(text);
        // server tips/hints (💡) surface as a soft toast instead of scrolling past
        if (/💡/.test(text)) {
          const line = text.split('\n').map(l => l.replace(/\x1b\[[0-9;]*m/g, '').trim())
            .find(l => l.includes('💡'));
          if (line) toast('💡 Tip', line.replace(/💡/g, '').trim(), 'tip');
        }
      });
      // small login nudge: if today's daily reward is unclaimed, invite a peek
      MH.bus.on('login.success', () => {
        setTimeout(async () => {
          try {
            const a = await (await fetch(`/almanac?player=${encodeURIComponent(MH.state.playerName)}`)).json();
            if (a.daily && !a.daily.claimed_today) toast('🌟 Daily reward ready', 'Press Y to claim · streak ' + a.daily.streak, 'daily');
          } catch (_) {}
        }, 2500);
      });

      // chat panel
      document.querySelectorAll('.chat-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          document.querySelectorAll('.chat-tab').forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          activeTab = tab.dataset.tab;
          if (unread[activeTab] !== undefined) unread[activeTab] = 0;
          renderChatBody();
          updateBadges();
        });
      });
      els.chatInput.addEventListener('focus', () => setTyping(true));
      els.chatInput.addEventListener('blur', () => setTyping(false));
      const emoteBtn = $('emote-btn');
      if (emoteBtn) emoteBtn.addEventListener('click', e => { e.stopPropagation(); emotePickerOpen(); });
      document.addEventListener('click', e => {
        const ep = $('emote-picker');
        if (ep && ep.classList.contains('show') && !ep.contains(e.target) && e.target.id !== 'emote-btn') emotePickerOpen(false);
      });
      els.chatInput.addEventListener('keydown', e => {
        e.stopPropagation();
        if (e.key === 'Enter') sendChat();
        else if (e.key === 'Escape') toggleChatPanel(false);
      });

      // minimap: click to travel, wheel / +/- to zoom
      els.minimap.addEventListener('click', minimapClick);
      els.mmToggle.addEventListener('click', toggleMinimapSize);
      els.minimap.addEventListener('wheel', e => {
        e.preventDefault();
        mmSetZoom(mmZoom + (e.deltaY < 0 ? 1 : -1));
      }, { passive: false });
      $('mm-in').addEventListener('click', () => mmSetZoom(mmZoom + 2));
      const helpBtn = $('help-btn');
      if (helpBtn) helpBtn.addEventListener('click', () => openHelp());
      // world map wiring
      $('wm-close').addEventListener('click', () => wmToggle(false));
      $('wm-zone').addEventListener('mousemove', e => {
        const tip = $('wm-tip');
        const h = wmNearest(e);
        if (!h) { tip.style.display = 'none'; return; }
        const rect = $('wm-body').getBoundingClientRect();
        tip.textContent = h.lit === false ? h.name + ' · uncharted' : h.name + ' · click to travel';
        tip.style.display = 'block';
        tip.style.left = Math.min(e.clientX - rect.left + 14, rect.width - 180) + 'px';
        tip.style.top = (e.clientY - rect.top - 26) + 'px';
      });
      $('wm-zone').addEventListener('click', e => {
        if (wmView !== 'zone') return;
        const h = wmNearest(e);
        if (!h) return;
        if (h.lit === false) { flash('You have not charted that room yet.'); return; }
        const p = MH.state.lastPayload && MH.state.lastPayload.player;
        if (p && h.vnum === p.vnum) { flash('You are here.'); return; }
        walkTargetVnum = h.vnum;
        renderMinimap();
        flash(`Walking to ${h.name}…`);
        wmToggle(false);
        walkStep();
      });
      window.addEventListener('keydown', e => {
        if (e.key === 'Escape' && wmOpen) wmToggle(false);
      });
      window.addEventListener('resize', () => { if (wmOpen) wmRender(); fitMinimapColumn(); });
      // the game owns right-click: no browser menu over the world
      document.addEventListener('contextmenu', e => {
        if (e.target.tagName === 'CANVAS' || e.target.closest('#game-root')) e.preventDefault();
      });
      MH.bus.on('room.entered', () => setTimeout(fitMinimapColumn, 80));
      setTimeout(fitMinimapColumn, 1200);
      window.addEventListener('keydown', e => {
        if (e.key.toLowerCase() === 'h' && !e.ctrlKey && !e.metaKey
            && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) openHelp();
      });
      // ↕ cycles through the levels you've explored here (sewers, towers)
      $('mm-level').addEventListener('click', () => {
        const payload = MH.state.lastPayload;
        const pz = (payload && payload.player && payload.player.z) || 0;
        const levels = [...new Set(((payload && payload.rooms) || []).map(r => (r.z || 0)))].sort((a, b) => b - a);
        if (levels.length < 2) { flash('Nothing explored above or below here yet.'); return; }
        const cur = levels.indexOf(pz + mmZOffset);
        const next = levels[(cur + 1) % levels.length];
        mmZOffset = next - pz;
        flash(mmZOffset === 0 ? 'Map: your level' : mmZOffset < 0 ? 'Map: below ground' : 'Map: upper level');
        renderMinimap();
      });
      $('mm-out').addEventListener('click', () => mmSetZoom(mmZoom - 2));

      // game events
      const updatePathChip = p => {
        if (!p) return;
        if (p.path_active === 'lone_wolf') { els.pathChip.textContent = '🐺 LONE WOLF'; els.pathChip.style.display = 'block'; els.pathChip.style.color = '#d8c8a0'; }
        else if (p.path_active === 'fellowship') { els.pathChip.textContent = '🤝 FELLOWSHIP'; els.pathChip.style.display = 'block'; els.pathChip.style.color = '#9ad0a8'; }
        else if (p.path) { els.pathChip.textContent = (p.path === 'lone_wolf' ? '🐺' : '🤝') + ' dormant'; els.pathChip.style.display = 'block'; els.pathChip.style.color = '#5a6070'; }
        else els.pathChip.style.display = 'none';
      };
      MH.bus.on('map', payload => { updateHud(payload.player); renderMinimap(); updateVignette(); autofillBar(); updatePathChip(payload.player); });
      // quest tracker: refresh on room change (cheap) + throttle
      let qtLastVnum = null;
      MH.bus.on('map', payload => {
        const v = payload.player && payload.player.vnum;
        if (v !== qtLastVnum) { qtLastVnum = v; refreshQuestTracker(true); }
        else refreshQuestTracker(false);
      });
      MH.bus.on('login.success', () => setTimeout(() => refreshQuestTracker(true), 1500));
      // first-spawn welcome for new players (once, level <= 2)
      let welcomeChecked = false;
      function maybeWelcome(player) {
        if (welcomeChecked || !player) return;
        welcomeChecked = true;
        if ((player.level || 1) > 2 || lsGet('mh_welcome_seen') === '1') return;
        els.welcomeBody.innerHTML =
          `Welcome, <b>${player.name || 'adventurer'}</b>. You stand in the Temple of Midgaard.<br><br>`
          + `<b>Sage Aldric</b> is here to set you on your path — look for the gold <b>!</b> floating above him, walk up, and click <b>Talk</b>. `
          + `Your current objective is always shown top-left and marked on your map (<b>◈</b>).<br><br>`
          + `Hostile creatures glow red — face one and press <b>F</b> to fight. You can do everything by typing too: press <b>Enter</b> for a command line.`;
        setWorldInput(false);
        els.welcomeOverlay.classList.add('show');
      }
      els.welcomeGo.addEventListener('click', () => {
        els.welcomeOverlay.classList.remove('show'); lsSet('mh_welcome_seen', '1'); setWorldInput(true);
      });
      MH.bus.on('map', payload => maybeWelcome(payload.player));
      MH.bus.on('combat.update', () => { updateHud(MH.state.player); updateVignette(); });
      MH.bus.on('room.entered', () => { walkStep(); hideMobTip(); renderCompass(); });
      // gentle onboarding for first-timers
      let hintsShown = false;
      MH.bus.on('map', () => {
        const p = MH.state.player;
        if (hintsShown || !p || (p.level || 99) > 2 || lsGet('misthollow_hints_done')) return;
        hintsShown = true;
        lsSet('misthollow_hints_done', '1');
        const hints = [
          'WASD to walk — step off a room edge to travel',
          'Golden ! marks someone with a quest — click friendly folk to talk',
          'F swings your weapon at hostile creatures · Tab picks targets',
          'Keys 1–0 use your action bar · K opens your abilities',
        ];
        hints.forEach((h, i) => setTimeout(() => flash(h), 1500 + i * 4200));
      });
      MH.bus.on('map', () => renderCompass());
      MH.bus.on('mob.tip', showMobTip);
      MH.bus.on('mob.tip.hide', hideMobTip);
      MH.bus.on('move.blocked', () => cancelWalk());
      MH.bus.on('player.death', () => cancelWalk());
      MH.bus.on('room.entered', ({ room, zoneName }) => showRoom(room, zoneName));
      MH.bus.on('flash', flash);
      MH.bus.on('move.blocked', e => {}); // scene flashes it
      MH.bus.on('chat', e => chatLine(e.line));
      MH.bus.on('target.set', setTarget);
      // live combat log: every exchange visible at a glance
      let clogHideTimer = null;
      const clogLine = (text, cls) => {
        const div = document.createElement('div');
        div.className = cls;
        div.textContent = text;
        els.combatLogLines.appendChild(div);
        while (els.combatLogLines.children.length > 7) els.combatLogLines.removeChild(els.combatLogLines.firstChild);
        els.combatLog.classList.add('show');
        clearTimeout(clogHideTimer);
        clogHideTimer = setTimeout(() => { if (!MH.state.inCombat) els.combatLog.classList.remove('show'); }, 4000);
      };
      MH.bus.on('combat.hit', e => clogLine(e.dmg != null ? `You hit ${e.target} for ${e.dmg}` : `You hit ${e.target}`, 'you'));
      MH.bus.on('combat.miss', e => clogLine(`You miss ${e.target}`, 'miss'));
      MH.bus.on('combat.dodged', () => clogLine('They miss you', 'miss'));
      MH.bus.on('mob.death', e => clogLine(`${e.name || 'It'} dies!`, 'info'));
      MH.bus.on('player.exp', e => clogLine(`+${e.amount} experience`, 'info'));
      MH.bus.on('combat.flee', () => clogLine('You flee!', 'info'));
      MH.bus.on('combat.state', on => {
        if (!on) { clearTimeout(clogHideTimer); clogHideTimer = setTimeout(() => els.combatLog.classList.remove('show'), 3000); }
        duelShow(on);
      });

      // duel card: you vs the foe, faces and life side by side
      let duelFoeName = null, duelHideTimer = null;
      const duelShow = on => {
        const card = $('duel-card');
        if (!card) return;
        clearTimeout(duelHideTimer);
        if (on) {
          card.classList.add('show');
          duelRenderYou();
          duelRenderFoes(MH.state.lastCombatMobs || (currentTarget ? [{ ...currentTarget, fighting: true }] : []));
        } else {
          duelHideTimer = setTimeout(() => card.classList.remove('show'), 2500);
        }
      };
      const duelRenderYou = () => {
        const src = document.getElementById('hud-portrait');
        const dst = document.getElementById('duel-you');
        const p = MH.state.player || {};
        if (src && dst) {
          const ctx = dst.getContext('2d');
          ctx.clearRect(0, 0, dst.width, dst.height);
          ctx.drawImage(src, 0, 0, src.width, src.height * 0.72, 0, 0, dst.width, dst.height);
        }
        const nm = document.getElementById('duel-you-nm');
        if (nm) nm.textContent = p.name || 'you';
        const bar = document.getElementById('duel-you-hp');
        if (bar) bar.style.width = `${Math.max(0, Math.min(100, ((p.hp || 0) / Math.max(1, p.max_hp || 1)) * 100))}%`;
      };
      // stacked foe frames: one row per mob fighting YOU, click to retarget
      const foePortraits = new Map();
      const duelRenderFoes = mobs => {
        const host = document.getElementById('duel-foes');
        if (!host) return;
        const foes = (mobs || []).filter(m => m.fighting);
        const SHOW = 4;
        host.innerHTML = '';
        for (const m of foes.slice(0, SHOW)) {
          const row = document.createElement('div');
          row.className = 'foe-row' + (currentTarget && currentTarget.name === m.name ? ' active' : '');
          const cv = document.createElement('canvas');
          cv.width = 30; cv.height = 26;
          row.appendChild(cv);
          const meta = document.createElement('div');
          meta.className = 'fr-meta';
          const pct = m.maxHp ? Math.max(0, Math.min(100, ((m.hp != null ? m.hp : m.maxHp) / m.maxHp) * 100)) : 100;
          meta.innerHTML = `<div class="fr-nm">${m.name}</div><div class="fr-hp"><i style="width:${pct}%"></i></div>`;
          row.appendChild(meta);
          row.title = `switch attacks to ${m.name}`;
          row.addEventListener('click', () => {
            const scene = MH.game && MH.game.scene.getScenes(true).find(sc => sc.targetByName);
            if (scene) scene.targetByName(m.name);
            MH.sendCommand(`kill ${MH.mobKeyword(m.name)}`);
          });
          host.appendChild(row);
          const scene = MH.game && MH.game.scene.getScenes(true).find(sc => sc.mobPortrait);
          if (scene) scene.mobPortrait(cv, m.name);
        }
        if (foes.length > SHOW) {
          const more = document.createElement('div');
          more.className = 'foe-more';
          more.textContent = `+${foes.length - SHOW} more`;
          host.appendChild(more);
        }
        if (!foes.length && currentTarget) duelRenderFoes([{ ...currentTarget, fighting: true }]);
      };
      MH.bus.on('combat.update', payload => { if ($('duel-card').classList.contains('show')) { duelRenderFoes(payload.mobs); duelRenderYou(); } });
      MH.bus.on('target.set', () => { if ($('duel-card').classList.contains('show')) {
        const pl = MH.state.lastCombatMobs;
        if (pl) duelRenderFoes(pl);
      } });

      // ===== party frames: top-center bar of allied unit frames =====
      const ROLE_ICON = { tank: '🛡', healer: '✚', dps: '⚔', pet: '🐾' };
      const DIR_ARROW = { north: '↑', south: '↓', east: '→', west: '←', up: '⤒', down: '⤓',
        northeast: '↗', northwest: '↖', southeast: '↘', southwest: '↙' };
      const FRIENDLY_SPELL = /cure|heal|bless|armor|shield|sanctuary|renew|mend|protection|haste|barkskin|aegis|prayer|serenity|hymn|lay_on_hands|spirit_link|hand_of_freedom/i;
      const prevHp = {};          // name -> last hp seen, for damage/heal pops
      const lowWarned = {};       // name -> already alerted at low hp
      let lastGroup = null;

      function partyHide() { els.partyBar.classList.remove('show'); els.partyBar.innerHTML = ''; }

      function frameFor(m, group) {
        const f = document.createElement('div');
        const hpPct = Math.max(0, Math.min(100, (m.hp / Math.max(1, m.maxHp)) * 100));
        const mpPct = Math.max(0, Math.min(100, (m.mana / Math.max(1, m.maxMana)) * 100));
        const crit = hpPct <= 30, mid = hpPct > 30 && hpPct <= 60;
        f.className = 'pf'
          + (m.is_self ? ' self' : '')
          + (m.is_minion ? ' minion' : '')
          + (!m.sameRoom ? ' away' : '')
          + (m.dead ? ' dead' : '')
          + (crit && !m.dead && m.sameRoom ? ' low' : '');
        f.dataset.name = m.name;
        const canHeal = group.heal_spell && m.sameRoom && !m.dead && !m.is_minion;
        f.innerHTML =
          `<div class="pf-top">`
          + `<span class="pf-role ${m.role}" title="${m.is_minion ? m.minion_kind : m.role}">${ROLE_ICON[m.role] || '⚔'}</span>`
          + `<span class="pf-nm">${m.is_leader ? '<span class="crown">♚</span>' : ''}${m.is_minion ? '<span style="color:#8a90a4">└ </span>' : ''}${m.name}</span>`
          + `<span class="pf-lv">L${m.level}</span></div>`
          + `<div class="pf-bar hp ${crit ? 'crit' : mid ? 'mid' : ''}"><i style="width:${hpPct}%"></i><b>${m.dead ? 'DEAD' : Math.round(m.hp) + '/' + m.maxHp}</b></div>`
          + (m.is_minion ? '' : `<div class="pf-bar mana"><i style="width:${mpPct}%"></i></div>`)
          + `<div class="pf-foot">`
          + (m.sameRoom
              ? `<span class="pf-target ${m.fighting ? '' : 'empty'}">${m.fighting ? '⚔ ' + m.fighting : 'idle'}</span>`
              : `<span class="pf-dir">${m.dir ? (DIR_ARROW[m.dir] || '•') + ' ' : '⋯ '}${m.roomName}</span>`)
          + (canHeal ? `<button class="pf-heal" title="heal ${m.name}">✚</button>` : '')
          + `</div>`;
        // left-click = assist that member (attack what they're fighting)
        if (!m.is_self && !m.is_minion) {
          f.addEventListener('click', () => {
            if (!m.sameRoom) { flash(`${m.name} is ${m.dir ? DIR_ARROW[m.dir] + ' ' : ''}${m.roomName}`); return; }
            if (m.fighting) MH.sendCommand(`assist ${m.name.split(' ')[0]}`);
            else { MH.state.allyTarget = { name: m.name.split(' ')[0], until: Date.now() + 15000 }; flash(`Focusing ${m.name}`); }
          });
        }
        if (!m.is_minion) f.addEventListener('contextmenu', e => { e.preventDefault(); e.stopPropagation(); partyMenu(m, group, e.clientX, e.clientY); });
        else f.addEventListener('contextmenu', e => { e.preventDefault(); e.stopPropagation(); flash(`${m.name} — ${m.minion_kind} · click Companions (C) to manage`); });
        const heal = f.querySelector('.pf-heal');
        if (heal) heal.addEventListener('click', e => {
          e.stopPropagation();
          MH.sendCommand(`cast ${group.heal_spell} ${m.name.split(' ')[0]}`);
          flash(`✚ healing ${m.name}`);
        });
        return f;
      }

      function partyMenu(m, group, x, y) {
        const menu = els.partyMenu;
        const me = group.members.find(mm => mm.is_self) || {};
        const kw = m.name.split(' ')[0];
        const items = [];
        if (!m.is_self) {
          items.push({ label: '🎯 Focus (heal/buff target)', fn: () => { MH.state.allyTarget = { name: kw, until: Date.now() + 30000 }; flash(`Focusing ${m.name}`); } });
          if (group.heal_spell && m.sameRoom) items.push({ label: `✚ Cast ${group.heal_spell.replace(/_/g, ' ')}`, fn: () => MH.sendCommand(`cast ${group.heal_spell} ${kw}`) });
          if (m.sameRoom && m.fighting) items.push({ label: `⚔ Assist (attack ${m.fighting})`, fn: () => MH.sendCommand(`assist ${kw}`) });
          items.push({ label: '💬 Whisper', fn: () => { els.chatMode.value = 'tell'; toggleChatPanel(true); els.chatInput.value = `${kw} `; els.chatInput.focus(); } });
          items.push({ label: '👁 Inspect', fn: () => MH.sendCommand(`consider ${kw}`) });
          items.push({ label: '🤝 Trade', fn: () => MH.sendCommand(`trade ${kw}`) });
          items.push({ label: '🔗 Follow', fn: () => MH.sendCommand(`follow ${kw}`) });
        }
        if (me.is_leader && !m.is_self) {
          items.push({ sep: true });
          items.push({ label: '♚ Make leader', fn: () => MH.sendCommand(`group leader ${kw}`) });
          items.push({ label: '✖ Remove from group', fn: () => MH.sendCommand(`group kick ${kw}`) });
        }
        if (me.is_leader && m.is_self) {
          items.push({ label: `Loot: ${group.loot_mode === 'roundrobin' ? 'Round-Robin → Free-for-All' : 'Free-for-All → Round-Robin'}`,
            fn: () => MH.sendCommand(`group loot ${group.loot_mode === 'roundrobin' ? 'freeforall' : 'roundrobin'}`) });
        }
        if (m.is_self) items.push({ label: '🚪 Leave group', fn: () => MH.sendCommand('group leave') });
        menu.innerHTML = `<div class="pm-hd">${m.name}${m.is_leader ? ' ♚' : ''} · ${m.role}</div>`;
        for (const it of items) {
          if (it.sep) { const s = document.createElement('div'); s.className = 'pm-sep'; menu.appendChild(s); continue; }
          const d = document.createElement('div'); d.className = 'pm-it'; d.textContent = it.label;
          d.addEventListener('click', () => { menu.style.display = 'none'; it.fn(); });
          menu.appendChild(d);
        }
        menu.style.display = 'block';
        const w = menu.offsetWidth || 160, h = menu.offsetHeight || 200;
        menu.style.left = Math.min(x, window.innerWidth - w - 8) + 'px';
        menu.style.top = Math.min(y, window.innerHeight - h - 8) + 'px';
      }
      document.addEventListener('click', e => {
        if (els.partyMenu.style.display === 'block' && !els.partyMenu.contains(e.target)) els.partyMenu.style.display = 'none';
      });

      function popNumber(name, delta) {
        const frame = els.partyBar.querySelector(`.pf[data-name="${(name || '').replace(/"/g, '')}"]`);
        if (!frame) return;
        const p = document.createElement('div');
        p.className = 'pf-pop';
        const heal = delta > 0;
        p.textContent = (heal ? '+' : '') + Math.round(delta);
        p.style.color = heal ? '#7fe09a' : '#ff8a7a';
        frame.appendChild(p);
        setTimeout(() => { if (p.parentNode) p.parentNode.removeChild(p); }, 950);
      }

      function renderParty(group) {
        if (!group || !group.members || group.size < 2) { partyHide(); lastGroup = null; return; }
        lastGroup = group;
        els.partyBar.innerHTML = '';
        // self first, then the rest in roster order
        const ordered = group.members.slice().sort((a, b) => (b.is_self - a.is_self) || (b.is_leader - a.is_leader));
        for (const m of ordered) {
          // floating combat numbers + low-hp alert, driven by vitals diff
          const last = prevHp[m.name];
          if (last != null && m.hp !== last && !m.dead) popNumber(m.name, m.hp - last);
          prevHp[m.name] = m.hp;
          const pct = (m.hp / Math.max(1, m.maxHp)) * 100;
          if (pct <= 30 && !m.dead && m.sameRoom) {
            if (!lowWarned[m.name]) { lowWarned[m.name] = true; if (!m.is_self) tone({ f: 880, f2: 660, type: 'sine', dur: 0.18, vol: 0.06 }); }
          } else { lowWarned[m.name] = false; }
          els.partyBar.appendChild(frameFor(m, group));
        }
        els.partyBar.classList.add('show');
      }
      MH.bus.on('map', payload => renderParty(payload.group));
      MH.bus.on('combat.update', payload => renderParty(payload.group));
      // WoW-style cast bar: starts on 'cast', completes when the spell lands
      let castTimer = null;
      const startCast = name => {
        els.castBar.querySelector('.nm').textContent = name;
        els.castBar.classList.remove('go', 'done');
        void els.castBar.offsetWidth;
        els.castBar.classList.add('show', 'go');
        clearTimeout(castTimer);
        castTimer = setTimeout(() => els.castBar.classList.remove('show', 'go', 'done'), 2600);
      };
      const endCast = ok => {
        if (!els.castBar.classList.contains('show')) return;
        els.castBar.classList.add('done');
        clearTimeout(castTimer);
        castTimer = setTimeout(() => els.castBar.classList.remove('show', 'go', 'done'), ok ? 450 : 250);
      };
      MH.bus.on('terminal.echo', cmd => {
        const m = String(cmd).match(/^cast '([^']+)'/i);
        if (m) startCast(m[1]);
      });
      MH.bus.on('combat.hit', () => endCast(true));
      MH.bus.on('combat.cast', () => endCast(true));
      MH.bus.on('player.heal', () => endCast(true));

      // next-exchange timer: MUD rounds are ~2s; show the rhythm
      MH.bus.on('combat.update', () => {
        els.roundBar.classList.add('show');
        els.roundBar.classList.remove('tick');
        void els.roundBar.offsetWidth;
        els.roundBar.classList.add('tick');
      });
      MH.bus.on('combat.state', on => { if (!on) els.roundBar.classList.remove('show', 'tick'); });

      // loot flow: corpse click -> loot toast -> inventory refreshed + opened
      let lootTimer = null;
      MH.bus.on('loot.corpse', async () => {
        const p = captureOutput(1300);
        MH.sendCommand('get all corpse', false);
        const lines = await p;
        const loot = lines.filter(l => /you get .+ from the corpse|there (?:is|are) no|corpse is empty|you can'?t/i.test(l));
        els.lootLines.innerHTML = '';
        (loot.length ? loot : ['The corpse holds nothing.']).slice(0, 8).forEach(l => {
          const div = document.createElement('div');
          div.className = /gold coin/i.test(l) ? 'gold' : 'it';
          const nm = l.replace(/^You get /i, '').replace(/ from the corpse\.?$/i, '');
          if (MH.itemIcons && loot.length) {
            const c = document.createElement('canvas');
            c.width = c.height = 20;
            c.style.verticalAlign = 'middle';
            c.style.marginRight = '5px';
            MH.itemIcons.intoCanvas(c, { name: nm });
            div.appendChild(c);
          }
          div.appendChild(document.createTextNode((loot.length ? '+ ' : '') + nm));
          els.lootLines.appendChild(div);
        });
        els.lootToast.classList.add('show');
        clearTimeout(lootTimer);
        lootTimer = setTimeout(() => els.lootToast.classList.remove('show'), 3500);
        await MH.refreshState();
        renderInventory();
        openModal('modal-inv');
      });

      // stance bar (warriors get all four; everyone can shift mood)
      const STANCES = ['battle', 'berserk', 'defensive', 'precision'];
      STANCES.forEach(st => {
        const div = document.createElement('div');
        div.className = 'stance';
        div.dataset.st = st;
        div.textContent = st.toUpperCase();
        div.addEventListener('click', () => commandWithPeek(`stance ${st}`));
        els.stanceBar.appendChild(div);
      });
      const setStance = st => {
        els.stanceBar.querySelectorAll('.stance').forEach(d =>
          d.classList.toggle('active', d.dataset.st === String(st || '').toLowerCase()));
      };
      MH.bus.on('combat.state', on => {
        els.stanceBar.classList.toggle('show', !!on);
        if (!on) { els.momentumChip.classList.remove('show'); els.finisherChip.classList.remove('show'); }
      });

      // momentum meter + finisher window, fed by the per-round push
      let lastTargetHp = null;
      const finisherFor = () => {
        const cls = String((MH.state.player || {}).char_class || '').toLowerCase();
        return cls === 'warrior' ? 'execute' : cls === 'assassin' ? 'vital' : cls === 'thief' ? 'backstab' : null;
      };
      // every class's signature resource gets the chip: momentum, faith,
      // luck, focus, holy power, soul shards, inspiration, intel
      const RES_ICON = { Momentum: '🔥', Luck: '🍀', Intel: '🗡', Faith: '🕯', 'Holy Power': '✨', Focus: '🎯', 'Soul Shards': '💀', Inspiration: '🎵' };
      const renderResourceChip = p => {
        const r = p.resource;
        if (r && r.value > 0) {
          const icon = RES_ICON[r.name] || '◆';
          // pips for small caps, n/max for big ones (Focus 0-100)
          const detail = r.max <= 10
            ? '●'.repeat(r.value) + '○'.repeat(Math.max(0, r.max - r.value))
            : `${r.value}/${r.max}`;
          els.momentumChip.textContent = `${icon} ${r.name.toUpperCase()} ${detail}`;
          els.momentumChip.classList.add('show');
        } else if (p.momentum > 0) {
          els.momentumChip.textContent = `🔥 MOMENTUM ×${p.momentum}`;
          els.momentumChip.classList.add('show');
        } else {
          els.momentumChip.classList.remove('show');
        }
      };
      MH.bus.on('map', payload => { if (payload.player) renderResourceChip(payload.player); });
      MH.bus.on('combat.update', payload => {
        MH.state.lastCombatMobs = payload.mobs;
        const p = payload.player || {};
        renderResourceChip(p);
        if (p.stance) setStance(p.stance);
        // finisher window: target under 22%
        const mob = (payload.mobs || []).find(m2 => m2.fighting);
        if (mob && mob.maxHp && mob.hp != null) {
          lastTargetHp = mob;
          const frac = mob.hp / mob.maxHp;
          const fin = finisherFor();
          els.finisherChip.classList.toggle('show', !!(payload.in_combat && frac > 0 && frac <= 0.22 && fin));
        }
      });
      const doFinisher = () => {
        const fin = finisherFor();
        if (!fin || !els.finisherChip.classList.contains('show')) return;
        const t = currentTarget ? ` ${MH.mobKeyword(currentTarget.name)}` : (lastTargetHp ? ` ${MH.mobKeyword(lastTargetHp.name)}` : '');
        MH.sendCommand(fin + t);
        els.finisherChip.classList.remove('show');
      };
      els.finisherChip.addEventListener('click', doFinisher);
      window.addEventListener('keydown', e => {
        if (e.key.toLowerCase() === 'r' && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) doFinisher();
      });

      // the chip pulses with each server combat round
      MH.bus.on('combat.update', () => {
        els.combatChip.style.transform = 'translateX(-50%) scale(1.12)';
        setTimeout(() => { els.combatChip.style.transform = 'translateX(-50%) scale(1)'; }, 140);
      });

      MH.bus.on('combat.taken', e => {
        clogLine(e && e.dmg != null ? `${e.from || 'They'} hit YOU for ${e.dmg}` : 'They hit YOU', 'them');
        els.hitFlash.classList.remove('go');
        void els.hitFlash.offsetWidth;
        els.hitFlash.classList.add('go');
        sfx.taken();
      });
      MH.bus.on('combat.hit', () => sfx.hit());
      MH.bus.on('combat.state', on => {
        els.combatChip.classList.toggle('show', on);
        if (on) sfx.engage();
      });
      MH.bus.on('player.death', () => sfx.death());
      MH.bus.on('level.up', () => sfx.level());
      MH.bus.on('room.entered', () => sfx.move());
      MH.bus.on('target.update', setTarget);
      MH.bus.on('target.clear', () => setTarget(null));
      MH.bus.on('level.up', e => flash(e.line));
      MH.bus.on('shop.open', openShop);
      MH.bus.on('training.open', openTraining);
      MH.bus.on('npc.talk', openDialogue);

      // command input
      els.commandInput.addEventListener('focus', () => setTyping(true));
      els.commandInput.addEventListener('blur', () => setTyping(false));
      els.commandInput.addEventListener('keydown', e => {
        e.stopPropagation();
        if (e.key === 'Enter') {
          const cmd = els.commandInput.value.trim();
          if (cmd) { MH.sendCommand(cmd); els.commandInput.value = ''; }
          els.commandInput.blur();
        } else if (e.key === 'Escape') {
          els.commandInput.value = '';
          els.commandInput.blur();
        }
      });

      // spellbook tab switching
      document.querySelectorAll('.mtab').forEach(t =>
        t.addEventListener('click', () => showSpellsTab(t.dataset.mtab)));
      // almanac tab switching
      document.querySelectorAll('#modal-almanac .mtab').forEach(t =>
        t.addEventListener('click', () => openAlmanac(t.dataset.atab)));
      // services tab switching
      document.querySelectorAll('#modal-services .mtab').forEach(t =>
        t.addEventListener('click', () => openServices(t.dataset.stab)));
      // stable tab switching
      document.querySelectorAll('#modal-stable .mtab').forEach(t =>
        t.addEventListener('click', () => openStable(t.dataset.ctab)));
      // legend tab switching
      document.querySelectorAll('#modal-legend .mtab').forEach(t =>
        t.addEventListener('click', () => openLegend(t.dataset.ltab)));

      const bd = $('modal-backdrop');
      if (bd) bd.addEventListener('click', closeModals);

      // modal close buttons
      document.querySelectorAll('.modal-head .x').forEach(x =>
        x.addEventListener('click', () => $(x.dataset.close).classList.remove('open')));

      loadHotbar();

      // global keys
      window.addEventListener('keydown', e => {
        const typingEls = [els.commandInput, els.loginName, els.loginPass, els.chatInput];
        if (typingEls.includes(document.activeElement)) return;
        if (e.key === 'Enter') { e.preventDefault(); els.commandInput.focus(); return; }
        if (e.key === 'Escape') {
          // universal un-stick: close panels and clear any wedged state
          closeModals();
          cancelWalk();
          MH.state.pendingMove = null;
          setTyping(false);
          return;
        }
        if (e.key === '`' || e.key === '~') { e.preventDefault(); els.drawer.classList.toggle('open'); return; }
        if (anyModalOpen()) return;
        // Shift+WASD = compass move, Shift+Q/E = up/down
        if (e.shiftKey) {
          const navKey = { w: 'north', a: 'west', s: 'south', d: 'east', q: 'up', e: 'down' }[e.key.toLowerCase()];
          if (navKey) { e.preventDefault(); MH.bus.emit('nav.goto', navKey); return; }
        }
        if (e.key >= '0' && e.key <= '9') { useHotbar(e.key === '0' ? 9 : Number(e.key) - 1); return; }
        const k = e.key.toLowerCase();
        if (k === 'i') { renderInventory(); openModal('modal-inv'); }
        else if (k === 'j') { openJournal(); }
        else if (k === 'k') { renderSpells(); openModal('modal-spells'); showSpellsTab('abilities'); }
        else if (k === 'n') { renderSpells(); openModal('modal-spells'); showSpellsTab('talents'); }
        else if (k === 't') { e.preventDefault(); toggleChatPanel(); }
        else if (k === 'm') { wmToggle(); }
        else if (k === 'y') { openAlmanac('daily'); }
        else if (k === 'b') { openServices('mail'); }
        else if (k === 'c') { openStable('pets'); }
        else if (k === 'l') { openLegend('prestige'); }
        if (['a', 'd', 'w', 's', 'arrowleft', 'arrowright', 'arrowup', 'arrowdown', ' '].includes(k)) {
          cancelWalk();
          // moving dismisses the room prose so it never blocks the view
          els.roomDesc.classList.remove('show');
        }
        if (e.key === ' ') e.preventDefault(); // don't scroll the page
      });
    },
  };
})();
