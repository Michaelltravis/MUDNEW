// Misthollow: ARPG-inspired UI layer.
//   Diablo        - liquid health/mana globes flanking the action bar,
//                   low-health pulse; potion belt with quick keys
//   Path of Exile - buff/debuff bar with timers; bottom XP strip;
//                   item tooltips with equipped-comparison
//   Dragon Warrior- typewriter encounter window ("A slime draws near!")
(() => {
  const MH = window.MH = window.MH || {};
  const $ = id => document.getElementById(id);

  // ================= Diablo globes =================
  const globes = { hp: { cur: 1, tgt: 1, c: null }, mana: { cur: 1, tgt: 1, c: null } };
  let wavePhase = 0;
  const bubbles = [];

  function drawGlobe(g, kind) {
    const c = g.c;
    if (!c) return;
    const x = c.getContext('2d');
    const W = c.width, H = c.height, R = W / 2 - 3;
    x.clearRect(0, 0, W, H);
    // glass back
    const bg = x.createRadialGradient(W / 2, H / 2, R * 0.2, W / 2, H / 2, R);
    bg.addColorStop(0, 'rgba(20,24,34,0.9)');
    bg.addColorStop(1, 'rgba(8,10,16,0.95)');
    x.fillStyle = bg;
    x.beginPath(); x.arc(W / 2, H / 2, R, 0, 7); x.fill();
    // liquid
    g.cur += (g.tgt - g.cur) * 0.08;
    const lvl = Math.max(0.02, Math.min(1, g.cur));
    const top = H / 2 + R - lvl * 2 * R;
    x.save();
    x.beginPath(); x.arc(W / 2, H / 2, R - 1.5, 0, 7); x.clip();
    const low = kind === 'hp' && lvl < 0.25;
    const pulse = low ? 0.75 + 0.25 * Math.sin(wavePhase * 4) : 1;
    const lg = x.createLinearGradient(0, top, 0, H);
    if (kind === 'hp') {
      lg.addColorStop(0, `rgba(${Math.round(232 * pulse)},60,60,0.95)`);
      lg.addColorStop(1, 'rgba(110,16,20,0.95)');
    } else {
      lg.addColorStop(0, 'rgba(86,110,232,0.95)');
      lg.addColorStop(1, 'rgba(28,32,120,0.95)');
    }
    x.fillStyle = lg;
    x.beginPath();
    x.moveTo(0, H);
    x.lineTo(0, top);
    for (let px = 0; px <= W; px += 4) {
      x.lineTo(px, top + Math.sin(wavePhase + px * 0.09) * 2.2 + Math.sin(wavePhase * 0.7 + px * 0.05) * 1.4);
    }
    x.lineTo(W, H);
    x.closePath(); x.fill();
    // bubbles rise through the liquid
    x.fillStyle = 'rgba(255,255,255,0.25)';
    for (const b of bubbles) {
      if (b.kind !== kind) continue;
      const by = H - b.t * (H - top - 6);
      if (by > top + 4) { x.beginPath(); x.arc(b.x * W, by, b.r, 0, 7); x.fill(); }
    }
    x.restore();
    // glass shine + rim
    const sh = x.createRadialGradient(W * 0.36, H * 0.3, 1, W * 0.36, H * 0.3, R * 0.7);
    sh.addColorStop(0, 'rgba(255,255,255,0.22)');
    sh.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = sh;
    x.beginPath(); x.arc(W / 2, H / 2, R - 1, 0, 7); x.fill();
    x.strokeStyle = low ? `rgba(255,90,80,${0.5 + 0.5 * Math.sin(wavePhase * 4)})` : 'rgba(180,160,110,0.65)';
    x.lineWidth = 2;
    x.beginPath(); x.arc(W / 2, H / 2, R, 0, 7); x.stroke();
  }

  function globesLoop() {
    wavePhase += 0.045;
    for (const b of bubbles) {
      b.t += b.v;
      if (b.t > 1) { b.t = 0; b.x = 0.25 + Math.random() * 0.5; }
    }
    drawGlobe(globes.hp, 'hp');
    drawGlobe(globes.mana, 'mana');
    requestAnimationFrame(globesLoop);
  }

  // ================= potion belt =================
  const VERB = { potion: 'use', food: 'eat', drink: 'drink', scroll: 'recite' };
  let beltItems = [];
  function renderBelt() {
    const host = $('belt');
    const p = MH.state.player;
    if (!host || !p) return;
    const groups = new Map();
    for (const it of (p.inventory || [])) {
      const t = it.item_type || it.type;
      if (!['potion', 'food', 'drink', 'scroll'].includes(t)) continue;
      const k = it.name;
      const g = groups.get(k) || { item: it, n: 0 };
      g.n++;
      groups.set(k, g);
    }
    // healing first - the Diablo reflex slot
    beltItems = [...groups.values()].sort((a, b) => {
      const heal = x => /heal|cure|restore/i.test(x.item.name) ? 0 : 1;
      return heal(a) - heal(b) || b.n - a.n;
    }).slice(0, 4);
    host.innerHTML = '';
    for (let i = 0; i < 4; i++) {
      const slot = document.createElement('div');
      slot.className = 'belt-slot' + (beltItems[i] ? '' : ' empty');
      if (i === 0) slot.innerHTML = '<span class="bkey">Q</span>';
      if (beltItems[i]) {
        const cv = document.createElement('canvas');
        cv.width = cv.height = 30;
        if (MH.itemIcons) MH.itemIcons.intoCanvas(cv, beltItems[i].item);
        slot.appendChild(cv);
        const n = document.createElement('span');
        n.className = 'bcount';
        n.textContent = beltItems[i].n;
        slot.appendChild(n);
        slot.title = `${beltItems[i].item.name} (click${i === 0 ? ' or Q' : ''})`;
        slot.addEventListener('click', () => useBelt(i));
      }
      host.appendChild(slot);
    }
  }
  function useBelt(i) {
    const b = beltItems[i];
    if (!b) return;
    const verb = VERB[b.item.item_type || b.item.type] || 'use';
    MH.sendCommand(`${verb} ${MH.mobKeyword(b.item.name)}`);
    setTimeout(() => MH.refreshState && MH.refreshState().then(renderBelt), 700);
  }

  // ================= PoE buff bar =================
  const GOOD = /bless|armor|shield|sanctuary|haste|strength|giant|invis|detect|protect|aid|regen|stone/i;
  const BAD = /poison|curse|blind|weaken|plague|slow|fear|web|paraly/i;
  function renderBuffs() {
    const host = $('buff-bar');
    const p = MH.state.player;
    if (!host || !p) return;
    const affs = (p.affects || []).slice(0, 10);
    host.innerHTML = '';
    for (const a of affs) {
      const chip = document.createElement('div');
      const bad = BAD.test(a.name || '');
      chip.className = 'buff-chip' + (bad ? ' bad' : GOOD.test(a.name || '') ? ' good' : '');
      const rem = a.remaining != null ? a.remaining : a.duration;
      chip.innerHTML = `<i>${bad ? '☠' : '✦'}</i>${(a.name || '?').replace(/_/g, ' ')}`
        + (rem != null && rem >= 0 ? `<b>${rem}</b>` : '');
      chip.title = `${a.name}${a.applies_to ? ` · ${a.applies_to} ${a.value > 0 ? '+' : ''}${a.value}` : ''}${rem != null ? ` · ${rem} ticks left` : ''}`;
      host.appendChild(chip);
    }
  }

  // ================= Dragon Warrior encounter window =================
  // single composer: one target string, one typewriter chasing it - later
  // messages extend or replace the target instead of racing intervals
  let dwTimer = null, dwTyping = null, dwTarget = '', dwStart = 0;
  const DW_CPS = 60;   // characters per second
  function dwType() {
    const el = $('dw-window');
    if (!el) return;
    // time-based so starved timers catch up instead of crawling
    const want = Math.min(dwTarget.length, Math.floor((performance.now() - dwStart) / 1000 * DW_CPS));
    el.textContent = dwTarget.slice(0, want);
    if (want >= dwTarget.length) { clearInterval(dwTyping); dwTyping = null; }
  }
  function dwShow(text, hold = 3400, extend = false) {
    const el = $('dw-window');
    if (!el) return;
    const wasShown = el.classList.contains('show');
    el.classList.add('show');
    if (extend && wasShown && dwTarget) {
      dwTarget += text;   // keep the elapsed clock: typed text stays put
    } else {
      dwTarget = text;
      dwStart = performance.now();
      el.textContent = '';
    }
    if (!dwTyping) dwTyping = setInterval(dwType, 24);
    clearTimeout(dwTimer);
    dwTimer = setTimeout(() => { el.classList.remove('show'); dwTarget = ''; }, hold);
  }
  let lastFoe = null;
  MH.bus.on('target.set', t => { if (t && t.name) lastFoe = t.name; });
  MH.bus.on('target.update', t => { if (t && t.name) lastFoe = t.name; });
  MH.bus.on('combat.state', on => {
    if (on) dwShow(`⚔ ${lastFoe ? `${cap(lastFoe)} draws near!` : 'An enemy draws near!'} Command?`);
  });
  MH.bus.on('mob.death', e => {
    const nm = (e && e.name) || lastFoe || 'the enemy';
    dwShow(`Thou hast defeated ${nm.toLowerCase()}!`, 2800);
  });
  MH.bus.on('player.exp', e => {
    if (e && e.amount) {
      const el = $('dw-window');
      if (el && el.classList.contains('show')) dwShow(` Thy experience increases by ${e.amount}!`, 3200, true);
    }
  });
  MH.bus.on('player.death', () => dwShow('Thou art dead.', 4000));
  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

  // ================= item tooltips with comparison =================
  const RARC = { common: '#c8ccd8', uncommon: '#5fc46a', rare: '#5a8ae8', epic: '#b06ce0', legendary: '#ffa838' };
  function affLines(item) {
    return (item.affects || []).map(a => {
      const v = a.value != null ? a.value : a.modifier;
      const to = (a.applies_to || a.location || '').replace(/_/g, ' ');
      if (v == null || !to) return null;
      return `<div class="${v >= 0 ? 'aff-up' : 'aff-dn'}">${v >= 0 ? '+' : ''}${v} ${to}</div>`;
    }).filter(Boolean).join('') || '<div class="aff-none">no enchantments</div>';
  }
  function showItemTip(item, x, y, compare) {
    const tip = $('item-tip');
    if (!tip || !item) return;
    const rc = item.set_id ? '#4ad0c0' : (RARC[item.rarity || 'common']);
    let html = `<div class="it-name" style="color:${rc}">${item.short || item.name}</div>`;
    html += `<div class="it-meta">${item.rarity && item.rarity !== 'common' ? item.rarity + ' ' : ''}${item.slot ? item.slot + ' · ' : ''}${item.item_type || item.type || ''}${item.set_id ? ' · set piece' : ''}</div>`;
    html += affLines(item);
    if (compare) {
      html += `<div class="it-vs">— equipped: <span style="color:${compare.set_id ? '#4ad0c0' : RARC[compare.rarity || 'common']}">${compare.short || compare.name}</span> —</div>`;
      html += affLines(compare);
    }
    tip.innerHTML = html;
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect();
    tip.style.left = Math.min(x + 16, window.innerWidth - r.width - 10) + 'px';
    tip.style.top = Math.max(8, Math.min(y - 10, window.innerHeight - r.height - 10)) + 'px';
  }
  document.addEventListener('mouseover', e => {
    const p = MH.state.player;
    if (!p) return;
    const cell = e.target.closest && e.target.closest('.inv-cell');
    const sock = e.target.closest && e.target.closest('.pd-socket:not(.empty)');
    if (cell) {
      const item = (p.inventory || [])[Number(cell.dataset.i)];
      if (item) {
        const cmp = item.slot && p.equipment ? p.equipment[item.slot] : null;
        showItemTip(item, e.clientX, e.clientY, cmp && cmp.name !== item.name ? cmp : null);
        return;
      }
    } else if (sock) {
      const item = p.equipment && p.equipment[sock.dataset.slot];
      if (item) { showItemTip(item, e.clientX, e.clientY, null); return; }
    }
    const tip = $('item-tip');
    if (tip) tip.style.display = 'none';
  });

  // ================= XP strip =================
  function renderXpStrip(p) {
    const el = $('xp-strip');
    if (!el || !p) return;
    const floor = p.exp_floor || 0, next = p.exp_to_level || 0;
    const frac = next > floor ? Math.max(0, Math.min(1, ((p.exp || 0) - floor) / (next - floor))) : 1;
    el.style.width = (frac * 100) + '%';
  }

  // ================= boot =================
  function init() {
    globes.hp.c = $('globe-hp');
    globes.mana.c = $('globe-mana');
    for (let i = 0; i < 14; i++) {
      bubbles.push({ kind: i % 2 ? 'hp' : 'mana', x: 0.25 + Math.random() * 0.5, t: Math.random(), v: 0.002 + Math.random() * 0.004, r: 1 + Math.random() * 1.8 });
    }
    globesLoop();
    window.addEventListener('keydown', e => {
      if (e.key.toLowerCase() === 'q' && !e.ctrlKey && !e.metaKey && !e.shiftKey
          && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) useBelt(0);
    });
    MH.bus.on('map', payload => {
      const p = payload.player;
      if (!p) return;
      globes.hp.tgt = (p.hp || 0) / Math.max(1, p.max_hp || 1);
      globes.mana.tgt = (p.mana || 0) / Math.max(1, p.max_mana || 1);
      renderBelt();
      renderBuffs();
      renderXpStrip(p);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
