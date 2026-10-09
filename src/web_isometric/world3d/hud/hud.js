// The 3D client's HUD: player frame, orbs and action bar, target frame, room/zone banner,
// toasts, chat log with command line, menu and settings. DOM over the WebGL canvas,
// driven by the shared net.js state (`map` payloads, `combat.update`, server text).
// Actions go out as bus events ('hud.attack', 'hud.ability', 'hud.flee') for main.js,
// which knows the target and plays the hero's animation.
const $ = s => document.querySelector(s);
const ls = { get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (_) {} } };

// class kits in the order they unlock (same order as the 2D client's action bar)
export const KIT = {
  warrior: ['bash', 'cleave', 'kick', 'execute', 'rally', 'rescue', 'charge'],
  paladin: ['censure', 'order_verdict', 'holy_smite', 'absolution', 'halo_of_reckoning', 'turn_undead', 'rescue', 'bash'],
  ranger: ['truesight_shot', 'wildbond_strike', 'loosing_storm', 'quarry_mark', 'call_lightning'],
  thief: ['backstab', 'circle', 'trip', 'low_blow', 'pocket_sand', 'jackpot'],
  assassin: ['backstab', 'mark', 'expose', 'vital', 'feint', 'execute_contract', 'fade'],
  mage: ['magic_missile', 'fireball', 'lightning_bolt', 'chill_touch', 'sleep', 'towerbolt'],
  necromancer: ['soul_bolt', 'chill_touch', 'soul_siphon', 'animate_dead', 'soul_reap'],
  cleric: ['holy_smite', 'cure_light', 'heal', 'turn_undead', 'bless', 'flamestrike'],
  bard: ['mockery', 'fascinate', 'crescendo', 'discordant_note', 'sleep'],
};
const SELF = new Set(['rally', 'cure_light', 'heal', 'bless', 'fade', 'absolution', 'halo_of_reckoning', 'animate_dead', 'crescendo']);
const ICON = id => /heal|cure|bless|absolution|rally/.test(id) ? '✚' : /fire|flame|bolt|lightning|missile|smite|storm/.test(id) ? '✹'
  : /shot|loosing|quarry/.test(id) ? '➶' : /sleep|fascinate|mockery|note|crescendo/.test(id) ? '♪'
  : /soul|chill|dead|reap/.test(id) ? '☠' : /backstab|circle|vital|execute|expose|mark|feint|contract/.test(id) ? '🗡'
  : /bash|kick|trip|low_blow|charge|cleave|rescue|censure|verdict/.test(id) ? '⚒' : '✦';

export function createHud() {
  const els = {
    pf: $('#player-frame'), tf: $('#target-frame'), banner: $('#banner'), toasts: $('#toasts'),
    mm: $('#minimap'), ab: $('#actionbar'), chat: $('#chat'), log: $('#log'), input: $('#chat-input'),
    menu: $('#menu'), settings: $('#settings'), slots: $('#slots'),
  };
  const st = { player: null, kitKey: '', slots: [], cooldowns: {}, cdAt: 0, target: null, history: [], hi: -1 };

  // ---- scale ----
  function applyScale() {
    const pref = ls.get('mh3d_ui') || 'auto';
    const w = window.innerWidth;
    const v = pref === 'auto' ? (w >= 1800 ? 1.05 : w >= 1400 ? 0.95 : w >= 1000 ? 0.85 : 0.72) : Number(pref) || 1;
    document.documentElement.style.setProperty('--ui', v);
  }
  window.addEventListener('resize', applyScale);
  applyScale();

  function showGame(on) {
    for (const k of ['pf', 'mm', 'ab', 'chat', 'menu']) els[k].classList.toggle('hidden', !on);
    fitChat();
    els.log.scrollTop = els.log.scrollHeight;
  }
  // the chat sits left of the action bar and never runs under it
  function fitChat() {
    if (els.ab.classList.contains('hidden')) return;
    const left = els.ab.getBoundingClientRect().left;
    const ui = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui')) || 1;
    els.chat.style.width = window.innerWidth <= 900 ? '' : `${Math.max(240, Math.min(430 * ui, left - 14 - 12))}px`;
  }
  window.addEventListener('resize', () => requestAnimationFrame(fitChat));

  // ---- player ----
  const pct = (a, b) => `${Math.max(0, Math.min(100, (b ? a / b : 0) * 100))}%`;
  function setPlayer(p) {
    if (!p) return;
    st.player = p;
    els.pf.querySelector('.name').textContent = p.name || '';
    els.pf.querySelector('.cls').textContent = `${(p.race || '').replace(/_/g, ' ')} ${p.char_class || ''}`.trim();
    els.pf.querySelector('.ini').textContent = (p.name || '?')[0].toUpperCase();
    els.pf.querySelector('.lvl').textContent = p.level || 1;
    els.pf.querySelector('.bar.hp b').style.width = pct(p.hp, p.max_hp);
    const res = p.resource && p.resource.max ? { cur: p.resource.value, max: p.resource.max, name: p.resource.name }
      : { cur: p.mana, max: p.max_mana, name: 'Mana' };
    els.pf.querySelector('.bar.mp b').style.width = pct(res.cur, res.max);
    const hpOrb = els.ab.querySelector('.orb.hp'), mpOrb = els.ab.querySelector('.orb.mp');
    hpOrb.querySelector('.fill').style.height = pct(p.hp, p.max_hp);
    hpOrb.querySelector('.val').textContent = `${p.hp}/${p.max_hp}`;
    mpOrb.querySelector('.fill').style.height = pct(res.cur, res.max);
    mpOrb.querySelector('.val').textContent = `${res.cur}/${res.max}`;
    mpOrb.querySelector('.lab').textContent = res.name;
    const floor = p.exp_floor || 0, next = p.exp_to_level || 0;
    $('#xpbar b').style.width = next > floor ? pct((p.exp || 0) - floor, next - floor) : '0%';
    $('#xpbar').title = `Experience: ${p.exp || 0}${next ? ` / ${next}` : ''}`;
    // buffs and debuffs
    const aff = Array.isArray(p.affects) ? p.affects : [];
    $('#buffs').innerHTML = aff.slice(0, 8).map(a => {
      const n = String(a.name || a.type || a.spell || '').replace(/_/g, ' ');
      const bad = /poison|curse|blind|slow|weak|stun|bleed|burn|fear|snare|root/.test(n);
      return n ? `<i class="${bad ? 'bad' : ''}">${n}</i>` : '';
    }).join('');
    st.cooldowns = p.cooldowns || {};
    st.cdAt = performance.now();
    buildKit(p);
    paintCooldowns();
  }

  // ---- action bar: easy to start (3 buttons at level 1), grows with level ----
  function buildKit(p) {
    const cls = String(p.char_class || '').toLowerCase();
    const order = KIT[cls] || [];
    const learned = new Set([...Object.keys(p.skills || {}), ...Object.keys(p.spells || {})]);
    const spells = new Set([...Object.keys(p.spells || {}), ...(p.class_spells || []).map(s => typeof s === 'string' ? s : s && s.name)]);
    let avail = order.filter(a => learned.has(a));
    if (!avail.length && order.length) avail = [order[0]];
    const lv = p.level || 1;
    const n = lv <= 5 ? 1 : lv <= 10 ? 3 : 8;
    const kit = avail.slice(0, n);
    const key = `${cls}|${kit.join(',')}`;
    if (key === st.kitKey) return;
    st.kitKey = key;
    st.slots = [{ id: 'attack', key: 'F', icon: '⚔', label: 'Attack' }]
      .concat(kit.map((id, i) => ({ id, key: String(i + 1), icon: ICON(id), label: id.replace(/_/g, ' '), spell: spells.has(id), self: SELF.has(id) })))
      .concat([{ id: 'flee', key: '', icon: '🏃', label: 'Flee' }]);
    els.slots.innerHTML = st.slots.map((s, i) =>
      `<div class="slot" data-i="${i}" title="${s.label}${s.key ? ` (${s.key})` : ''}"><span class="key">${s.key}</span>`
      + `<div><div class="ic">${s.icon}</div><div class="ab">${s.label}</div></div></div>`).join('');
    els.slots.querySelectorAll('.slot').forEach(el => el.addEventListener('click', () => use(st.slots[+el.dataset.i])));
    requestAnimationFrame(fitChat);
  }
  function use(s) {
    if (!s) return;
    const el = els.slots.querySelector(`.slot[data-i="${st.slots.indexOf(s)}"]`);
    if (el) { el.classList.add('flash'); setTimeout(() => el.classList.remove('flash'), 180); }
    if (s.id === 'attack') MH.bus.emit('hud.attack');
    else if (s.id === 'flee') MH.bus.emit('hud.flee');
    else MH.bus.emit('hud.ability', { id: s.id, spell: s.spell, self: s.self });
  }
  function paintCooldowns() {
    const el = els.slots;
    const elapsed = (performance.now() - st.cdAt) / 1000;
    st.slots.forEach((s, i) => {
      const left = (st.cooldowns[s.id] || 0) - elapsed;
      const slot = el.querySelector(`.slot[data-i="${i}"]`);
      if (!slot) return;
      let cd = slot.querySelector('.cd');
      if (left > 0.05) {
        if (!cd) { cd = document.createElement('div'); cd.className = 'cd'; slot.appendChild(cd); }
        cd.textContent = left >= 10 ? Math.ceil(left) : left.toFixed(1);
      } else if (cd) cd.remove();
    });
  }
  setInterval(paintCooldowns, 200);

  // ---- target ----
  function setTarget(t) {
    st.target = t;
    els.tf.classList.toggle('hidden', !t);
    if (!t) return;
    els.tf.className = 'hud panel ' + (t.kind === 'player' ? 'ally' : t.hostile ? 'hostile' : (t.shopkeeper || t.trainer) ? 'npc' : 'neutral');
    els.tf.querySelector('.tname').textContent = t.name;
    const me = st.player ? st.player.level || 1 : 1;
    const diff = (t.level || 1) - me;
    const con = t.kind === 'player' ? 'Player' : diff >= 5 ? 'Deadly' : diff >= 3 ? 'Hard' : diff >= -2 ? 'Even match' : diff >= -5 ? 'Easy' : 'Trivial';
    const role = t.shopkeeper ? ' · shopkeeper' : t.trainer ? ' · trainer' : t.boss ? ' · boss' : '';
    els.tf.querySelector('.tsub').textContent = `Level ${t.level || '?'} · ${con}${role}`;
    els.tf.querySelector('.bar b').style.width = t.maxHp ? pct(t.hp, t.maxHp) : '100%';
  }
  els.tf.querySelector('.tclose').addEventListener('click', () => MH.bus.emit('hud.untarget'));

  // ---- banner + toasts ----
  let bannerTimer = 0;
  function banner(room, zone) {
    els.banner.querySelector('.zone').textContent = zone || '';
    els.banner.querySelector('.room').textContent = room || '';
    els.banner.style.opacity = 1;
    clearTimeout(bannerTimer);
    bannerTimer = setTimeout(() => { els.banner.style.opacity = 0; }, zone ? 3200 : 1800);
  }
  function toast(msg) {
    if (!msg) return;
    const d = document.createElement('div');
    d.textContent = msg;
    els.toasts.appendChild(d);
    while (els.toasts.children.length > 3) els.toasts.firstChild.remove();
    setTimeout(() => d.remove(), 2900);
  }

  // ---- chat log + command line ----
  const PROMPT = /^\s*<?\s*\d+\/\d+\s*hp\b[^\n]*>\s*$/i;
  let stick = true;
  els.log.addEventListener('scroll', () => { stick = els.log.scrollTop + els.log.clientHeight >= els.log.scrollHeight - 30; });
  function log(html, cls) {
    const atBottom = stick;
    const d = document.createElement('div');
    if (cls) { d.className = cls; d.textContent = html; } else d.innerHTML = html;
    els.log.appendChild(d);
    while (els.log.childElementCount > 400) els.log.firstChild.remove();
    if (atBottom) els.log.scrollTop = els.log.scrollHeight;
  }
  MH.bus.on('terminal.output', ({ html }) => {
    if (!html || !MH.state.isLoggedIn) return;
    const lines = String(html).split(/\r?\n/).filter(l => l.replace(/<[^>]+>/g, '').trim() && !PROMPT.test(l.replace(/<[^>]+>/g, '')));
    if (lines.length) log(lines.join('\n'));
  });
  MH.bus.on('terminal.echo', cmd => log(`> ${cmd}`, 'cmd'));
  els.input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const v = els.input.value.trim();
      if (v) { MH.sendCommand(v); st.history.unshift(v); st.history.length = Math.min(st.history.length, 50); }
      st.hi = -1;
      els.input.value = '';
      els.input.blur();
      e.preventDefault();
    } else if (e.key === 'Escape') { els.input.value = ''; els.input.blur(); }
    else if (e.key === 'ArrowUp' && st.history.length) { st.hi = Math.min(st.hi + 1, st.history.length - 1); els.input.value = st.history[st.hi]; e.preventDefault(); }
    else if (e.key === 'ArrowDown') { st.hi = Math.max(st.hi - 1, -1); els.input.value = st.hi >= 0 ? st.history[st.hi] : ''; e.preventDefault(); }
    e.stopPropagation();
  });

  // ---- menu + settings ----
  els.menu.querySelectorAll('button[data-cmd]').forEach(b => b.addEventListener('click', () => MH.sendCommand(b.dataset.cmd)));
  els.menu.querySelector('[data-act="settings"]').addEventListener('click', () => els.settings.classList.toggle('hidden'));
  const syncSettings = () => {
    const q = ls.get('mh3d_quality') || 'high', u = ls.get('mh3d_ui') || 'auto';
    els.settings.querySelectorAll('[data-set="quality"] button').forEach(b => b.classList.toggle('on', b.dataset.v === q));
    els.settings.querySelectorAll('[data-set="ui"] button').forEach(b => b.classList.toggle('on', b.dataset.v === u));
  };
  els.settings.querySelectorAll('[data-set="quality"] button').forEach(b => b.addEventListener('click', () => {
    ls.set('mh3d_quality', b.dataset.v); syncSettings();
    toast('Graphics quality changes after a reload');
  }));
  els.settings.querySelectorAll('[data-set="ui"] button').forEach(b => b.addEventListener('click', () => {
    ls.set('mh3d_ui', b.dataset.v); applyScale(); syncSettings();
  }));
  els.settings.querySelector('[data-act="perf"]').addEventListener('click', () => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'F3' })));
  els.settings.querySelector('[data-act="classic"]').addEventListener('click', () => window.open('/platformer', '_blank'));
  syncSettings();

  // ---- keys (when not typing) ----
  window.addEventListener('keydown', e => {
    if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
    if (!MH.state.isLoggedIn) return;
    const k = e.key;
    if (k === 'Enter') { els.input.focus(); e.preventDefault(); return; }
    if (k === 'f' || k === 'F' || k === ' ') { use(st.slots[0]); e.preventDefault(); return; }
    if (/^[1-8]$/.test(k)) { use(st.slots.find(s => s.key === k)); e.preventDefault(); return; }
    if (k === 'Escape') { MH.bus.emit('hud.untarget'); els.settings.classList.add('hidden'); return; }
    if (k === 'Tab') { MH.bus.emit('hud.cycleTarget'); e.preventDefault(); return; }
    const cmd = { c: 'score', i: 'inventory', k: 'spells', l: 'quests' }[k.toLowerCase()];
    if (cmd && !e.ctrlKey && !e.metaKey && !e.altKey) { MH.sendCommand(cmd); e.preventDefault(); }
  });

  return { showGame, setPlayer, setTarget, banner, toast, log, get player() { return st.player; } };
}
