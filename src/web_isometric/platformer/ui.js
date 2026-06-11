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
      capture = { lines: [], timer: setTimeout(() => { const l = capture.lines; capture = null; resolve(l); }, ms) };
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
    } else if (/^cast '[^']+'$/.test(cmd) && currentTarget) {
      MH.sendCommand(`${cmd} ${MH.mobKeyword(currentTarget.name)}`);
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
  let descTimer = null;
  let lastRoomShown = null;
  function showRoom(room, zoneName) {
    lastRoomShown = { room, zoneName };
    els.roomName.textContent = room.name || '';
    els.roomZone.textContent = zoneName || '';
    const desc = (room.description || '').trim();
    if (desc) {
      els.roomDesc.textContent = desc;
      els.roomDesc.classList.add('show');
      clearTimeout(descTimer);
      descTimer = setTimeout(() => els.roomDesc.classList.remove('show'), 4800);
    } else {
      els.roomDesc.classList.remove('show');
    }
  }

  // ---- flash line ----
  let flashTimer = null;
  function flash(text) {
    els.flashLine.textContent = text;
    els.flashLine.classList.add('show');
    clearTimeout(flashTimer);
    flashTimer = setTimeout(() => els.flashLine.classList.remove('show'), 2200);
  }

  // ---- chat: tabbed panel + ambient overlay ----
  const chatStore = { all: [], say: [], channel: [], tell: [] };
  const unread = { say: 0, channel: 0, tell: 0 };
  let activeTab = 'all';

  function classifyChat(line) {
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

  function sendChat() {
    const msg = els.chatInput.value.trim();
    if (!msg) return;
    const mode = els.chatMode.value;
    MH.sendCommand(mode === 'reply' ? `reply ${msg}` : `${mode} ${msg}`);
    els.chatInput.value = '';
  }

  // ---- modals ----
  function openModal(id) {
    closeModals();
    $(id).classList.add('open');
    const bd = $('modal-backdrop');
    if (bd) bd.classList.add('show');
  }
  function closeModals() {
    document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
    const bd = $('modal-backdrop');
    if (bd) bd.classList.remove('show');
  }
  function anyModalOpen() { return !!document.querySelector('.modal.open'); }

  function renderInventory() {
    const p = MH.state.player;
    if (!p) { els.invBody.textContent = 'No data yet.'; return; }
    let html = '<div style="color:#e8c168">— EQUIPPED —</div>';
    const eq = p.equipment || {};
    if (!Object.keys(eq).length) html += '<div class="slot">nothing equipped</div>';
    for (const [slot, item] of Object.entries(eq)) {
      html += `<div class="item" data-cmd="remove ${MH.mobKeyword(item.name)}"><span class="slot">[${slot}]</span> ${item.name} <span class="slot">(click to remove)</span></div>`;
    }
    html += '<div style="color:#e8c168;margin-top:8px">— CARRIED —</div>';
    const inv = p.inventory || [];
    if (!inv.length) html += '<div class="slot">empty-handed</div>';
    for (const item of inv) {
      html += `<div class="item" data-cmd="wear ${MH.mobKeyword(item.name)}">${item.name} <span class="slot">(${item.item_type || 'item'} · click to wear/wield)</span></div>`;
    }
    els.invBody.innerHTML = html;
    els.invBody.querySelectorAll('.item').forEach(el => el.addEventListener('click', () => {
      let cmd = el.dataset.cmd;
      if (cmd.startsWith('wear ') && /weapon/.test(el.textContent)) cmd = cmd.replace('wear ', 'wield ');
      MH.sendCommand(cmd);
      setTimeout(() => { MH.refreshState().then(renderInventory); }, 600);
    }));
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
        const prof = skills[s] != null ? `<span class="prof">${skills[s]}%</span>` : '';
        h += `<div class="spell-entry" draggable="true" data-cmd="${cmd}" data-kind="${isSpell ? 'sparkle' : 'star'}">`
          + `<canvas width="20" height="20"></canvas><span class="nm">${pretty}</span>${prof}</div>`;
      }
      return h + '</div>';
    };
    html += section('SKILLS', p.class_skills || [], false);
    html += section('SPELLS', p.class_spells || [], true);
    els.spellsBody.innerHTML = html;
    els.spellsBody.querySelectorAll('.spell-entry').forEach(el => {
      drawIcon(el.querySelector('canvas'), el.dataset.kind);
      el.addEventListener('click', () => {
        const t = currentTarget ? ` ${MH.mobKeyword(currentTarget.name)}` : '';
        MH.sendCommand(el.dataset.cmd + t);
        closeModals();
      });
      el.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', el.dataset.cmd));
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

  async function openJournal() {
    openModal('modal-journal');
    els.journalBody.textContent = 'Consulting your journal…';
    const p = captureOutput(1400);
    MH.sendCommand('quests', false);
    const lines = await p;
    els.journalBody.textContent = lines.length ? lines.join('\n') : 'The journal stays blank. (No active quests, or try `quest list`.)';
  }

  async function openShop(keeper) {
    openModal('modal-shop');
    els.shopBody.textContent = `${keeper ? keeper.name : 'The shopkeeper'} shows you the wares…`;
    const p = captureOutput(1400);
    MH.sendCommand('list', false);
    const lines = await p;
    if (!lines.length) { els.shopBody.textContent = 'No wares on offer here.'; return; }
    els.shopBody.innerHTML = '';
    for (const line of lines) {
      const div = document.createElement('div');
      div.className = 'item';
      div.textContent = line;
      div.addEventListener('click', () => {
        // try the last word of the listing as the buy keyword
        const kw = MH.mobKeyword(line.replace(/\d+|gold|coins?/gi, ''));
        if (kw && kw !== 'mob') { MH.sendCommand(`buy ${kw}`); setTimeout(() => MH.refreshState(), 600); }
      });
      els.shopBody.appendChild(div);
    }
    const hint = document.createElement('div');
    hint.className = 'slot';
    hint.textContent = '(click a line to buy; `sell <item>` via command input)';
    els.shopBody.appendChild(hint);
  }

  // ---- minimap + click-to-walk ----
  const MM_OFFSETS = { north: [0, -1, 0], south: [0, 1, 0], east: [1, 0, 0], west: [-1, 0, 0], up: [0, 0, 1], down: [0, 0, -1] };
  let mmLarge = false;
  let walkTargetVnum = null;
  let mmZoom = Number(lsGet('misthollow_mm_zoom')) || 9;

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
    const z = p.z || 0;
    const cell = mmCell();
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
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(W / 2 - 2, H / 2 - 2, 4, 4);
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
    const room = (payload.rooms || []).find(r => r.x === rx && r.y === ry && (r.z || 0) === (p.z || 0));
    if (!room || room.vnum === p.vnum) return;
    walkTargetVnum = room.vnum;
    renderMinimap();
    flash(`Walking to ${room.name}…`);
    walkStep();
  }

  function toggleMinimapSize() {
    mmLarge = !mmLarge;
    els.minimap.width = mmLarge ? 300 : 170;
    els.minimap.height = mmLarge ? 230 : 130;
    renderMinimap();
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
    let html = pathCardsHtml();
    html += `<div class="talent-points">★ ${data.points_available} talent point${data.points_available === 1 ? '' : 's'} available`
      + ` <span style="color:#7a8094">(${data.points_total} total · earned by leveling)</span></div>`;
    html += '<div class="ttrees">';
    for (const tree of data.trees) {
      html += `<div class="ttree"><div class="thead">`
        + `<div class="ticon">${tree.icon || '✦'}</div>`
        + `<div class="tname">${tree.name}</div>`
        + `<div class="tpts">${tree.points} points spent</div>`
        + `<div class="tdesc">${tree.description || ''}</div></div>`;
      const byTier = {};
      tree.talents.forEach(t => (byTier[t.tier] = byTier[t.tier] || []).push(t));
      const learnedIds = {};
      tree.talents.forEach(t => { if (t.rank > 0) learnedIds[t.id] = t.rank; });
      for (const tier of Object.keys(byTier).sort((a, b) => a - b)) {
        const need = (tier - 1) * 5;
        html += `<div class="tier-label">TIER ${tier}${need ? ` · ${need} pts in tree` : ''}</div>`;
        for (const t of byTier[tier]) {
          const tierOpen = tree.points >= need;
          const prereqMet = (t.requires || []).every(r => {
            const all = data.trees.flatMap(tr => tr.talents);
            const pre = all.find(x => x.id === r);
            return pre && pre.rank > 0;
          });
          const maxed = t.rank >= t.max_rank;
          const learnable = !maxed && tierOpen && prereqMet && data.points_available > 0;
          const cls = maxed ? 'tnode maxed' : learnable ? 'tnode learnable' : t.rank > 0 ? 'tnode ranked' : 'tnode locked';
          const reqTxt = (t.requires || []).length ? ` · requires: ${t.requires.join(', ')}` : '';
          html += `<div class="${cls}" data-tid="${t.id}" data-learnable="${learnable ? 1 : ''}"`
            + ` title="${(t.description || '').replace(/"/g, '&quot;')}${reqTxt}">`
            + `<span class="tn-name">${t.name}</span>`
            + `<span class="tn-rank">${t.rank}/${t.max_rank}</span></div>`;
        }
      }
      html += '</div>';
    }
    html += '</div>';
    els.talentsBody.innerHTML = html;
    wirePathButtons(els.talentsBody);
    els.talentsBody.querySelectorAll('.tnode[data-learnable="1"]').forEach(el => {
      el.addEventListener('click', async () => {
        MH.sendCommand(`talents learn ${el.dataset.tid}`);
        setTimeout(() => { renderTalents(); MH.refreshState(); }, 700);
      });
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
    let html = pathCardsHtml();
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
    els.talentsBody.innerHTML = html;
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
        }
      });
      MH.bus.on('terminal.echo', cmd => appendTerminal(`> ${cmd}`, 'cmd'));
      els.drawerTab.addEventListener('click', () => els.drawer.classList.toggle('open'));

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
      });
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
          div.textContent = l.replace(/^You get /i, '+ ').replace(/ from the corpse\.?$/i, '');
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
      MH.bus.on('combat.update', payload => {
        const p = payload.player || {};
        if (p.momentum > 0) {
          els.momentumChip.textContent = `🔥 MOMENTUM ×${p.momentum}`;
          els.momentumChip.classList.add('show');
        } else {
          els.momentumChip.classList.remove('show');
        }
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
        else if (k === 'm') { toggleMinimapSize(); }
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
