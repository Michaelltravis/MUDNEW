// Misthollow platformer: DOM overlays.
// Room prose banner, HUD bars, hotbar, raw-MUD terminal drawer, chat overlay,
// inventory/journal/shop/spell modals. Everything is driven by map payloads
// plus parser events; every action funnels back through real MUD commands.
(() => {
  const MH = window.MH = window.MH || {};
  const NAME_KEY = 'misthollow_name';
  const PW_KEY = 'misthollow_pw';
  const HOTBAR_KEY = 'misthollow_plat_hotbar';
  const DEFAULT_HOTBAR = ['kill', 'look', 'flee', 'rest', 'stand', 'inventory', 'score', 'quests'];

  const $ = id => document.getElementById(id);
  const els = {};

  function lsGet(k) { try { return localStorage.getItem(k); } catch (_) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (_) {} }

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

  // ---- hotbar ----
  let hotbar = [];
  function loadHotbar() {
    try { hotbar = JSON.parse(lsGet(HOTBAR_KEY)) || DEFAULT_HOTBAR.slice(); }
    catch (_) { hotbar = DEFAULT_HOTBAR.slice(); }
    if (!Array.isArray(hotbar) || hotbar.length !== 8) hotbar = DEFAULT_HOTBAR.slice();
    renderHotbar();
  }
  function renderHotbar() {
    els.hotbar.innerHTML = '';
    hotbar.forEach((cmd, i) => {
      const slot = document.createElement('div');
      slot.className = 'hotslot';
      slot.innerHTML = `<span class="key">${i + 1}</span><span class="lbl">${cmd || '—'}</span>`;
      slot.title = `${cmd}\n(right-click to rebind)`;
      slot.addEventListener('click', () => useHotbar(i));
      slot.addEventListener('contextmenu', e => {
        e.preventDefault();
        const next = prompt(`Command for slot ${i + 1}:`, hotbar[i] || '');
        if (next !== null) { hotbar[i] = next.trim(); lsSet(HOTBAR_KEY, JSON.stringify(hotbar)); renderHotbar(); }
      });
      els.hotbar.appendChild(slot);
    });
  }
  function useHotbar(i) {
    const cmd = hotbar[i];
    if (!cmd) return;
    // contextual targeting: "kill" or "cast 'x'" alone get the current target appended
    const t = currentTarget ? MH.mobKeyword(currentTarget.name) : '';
    if ((cmd === 'kill' || /^cast '[^']+'$/.test(cmd)) && t) MH.sendCommand(`${cmd} ${t}`);
    else MH.sendCommand(cmd);
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
  }

  // ---- target frame ----
  let currentTarget = null;
  function setTarget(data) {
    currentTarget = data;
    if (!data) { els.targetFrame.classList.remove('show'); return; }
    els.targetFrame.classList.add('show');
    els.targetName.textContent = `${data.name} (Lv ${data.level || '?'})`;
    const max = data.maxHp || 1, hp = data.hp != null ? data.hp : max;
    els.targetHp.style.width = `${Math.max(0, Math.min(100, (hp / max) * 100))}%`;
    els.targetHpTxt.textContent = `${hp} / ${max}`;
  }

  // ---- room banner / description ----
  let descTimer = null;
  function showRoom(room, zoneName) {
    els.roomName.textContent = room.name || '';
    els.roomZone.textContent = zoneName || '';
    const desc = (room.description || '').trim();
    if (desc) {
      els.roomDesc.textContent = desc;
      els.roomDesc.classList.add('show');
      clearTimeout(descTimer);
      descTimer = setTimeout(() => els.roomDesc.classList.remove('show'), 6500);
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
  function openModal(id) { closeModals(); $(id).classList.add('open'); }
  function closeModals() { document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open')); }
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
    let html = '<div style="color:#e8c168">— SKILLS —</div>';
    const list = (p.class_skills || []);
    if (!list.length) html += '<div class="slot">none</div>';
    for (const s of list) {
      html += `<div class="item" data-cmd="${s}">${s} <span class="slot">${skills[s] != null ? skills[s] + '%' : ''}</span></div>`;
    }
    html += '<div style="color:#e8c168;margin-top:8px">— SPELLS —</div>';
    const spells = (p.class_spells || []);
    if (!spells.length) html += '<div class="slot">none</div>';
    for (const s of spells) {
      html += `<div class="item" data-cmd="cast '${s}'">${s} <span class="slot">${skills[s] != null ? skills[s] + '%' : ''} (click to cast)</span></div>`;
    }
    els.spellsBody.innerHTML = html;
    els.spellsBody.querySelectorAll('.item').forEach(el => el.addEventListener('click', () => {
      const t = currentTarget ? ` ${MH.mobKeyword(currentTarget.name)}` : '';
      MH.sendCommand(el.dataset.cmd + t);
      closeModals();
    }));
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
        targetFrame: $('target-frame'), targetName: $('target-name'), targetHp: $('target-hp'), targetHpTxt: $('target-hp-txt'),
        hotbar: $('hotbar'), commandInput: $('command-input'),
        drawer: $('drawer'), drawerLog: $('drawer-log'), drawerTab: $('drawer-tab'),
        chatLog: $('chat-log'), chatPanel: $('chat-panel'), chatBody: $('chat-body'),
        chatInput: $('chat-input'), chatMode: $('chat-mode'),
        invBody: $('inv-body'), journalBody: $('journal-body'), shopBody: $('shop-body'), spellsBody: $('spells-body'),
      });

      // login
      const savedName = lsGet(NAME_KEY), savedPw = lsGet(PW_KEY);
      if (savedName) els.loginName.value = savedName;
      if (savedPw) { try { els.loginPass.value = atob(savedPw); } catch (_) {} }
      const begin = create => {
        const name = els.loginName.value.trim(), pass = els.loginPass.value;
        if (!name || !pass) { els.loginStatus.textContent = 'Need both name and password.'; els.loginStatus.className = 'error'; return; }
        MH.connect(name, pass, create);
      };
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

      // game events
      MH.bus.on('map', payload => updateHud(payload.player));
      MH.bus.on('combat.update', () => updateHud(MH.state.player));
      MH.bus.on('room.entered', ({ room, zoneName }) => showRoom(room, zoneName));
      MH.bus.on('flash', flash);
      MH.bus.on('move.blocked', e => {}); // scene flashes it
      MH.bus.on('chat', e => chatLine(e.line));
      MH.bus.on('target.set', setTarget);
      MH.bus.on('target.update', setTarget);
      MH.bus.on('target.clear', () => setTarget(null));
      MH.bus.on('level.up', e => flash(e.line));
      MH.bus.on('shop.open', openShop);

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

      // modal close buttons
      document.querySelectorAll('.modal-head .x').forEach(x =>
        x.addEventListener('click', () => $(x.dataset.close).classList.remove('open')));

      loadHotbar();

      // global keys
      window.addEventListener('keydown', e => {
        const typingEls = [els.commandInput, els.loginName, els.loginPass, els.chatInput];
        if (typingEls.includes(document.activeElement)) return;
        if (e.key === 'Enter') { e.preventDefault(); els.commandInput.focus(); return; }
        if (e.key === 'Escape') { closeModals(); return; }
        if (e.key === '`' || e.key === '~') { e.preventDefault(); els.drawer.classList.toggle('open'); return; }
        if (anyModalOpen()) return;
        if (e.key >= '1' && e.key <= '8') { useHotbar(Number(e.key) - 1); return; }
        const k = e.key.toLowerCase();
        if (k === 'i') { renderInventory(); openModal('modal-inv'); }
        else if (k === 'j') { openJournal(); }
        else if (k === 'k') { renderSpells(); openModal('modal-spells'); }
        else if (k === 't') { e.preventDefault(); toggleChatPanel(); }
        if (e.key === ' ') e.preventDefault(); // don't scroll the page
      });
    },
  };
})();
