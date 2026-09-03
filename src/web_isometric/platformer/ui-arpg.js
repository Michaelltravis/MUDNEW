// Misthollow: ARPG-inspired UI layer.
//   Diablo        - liquid health/mana globes flanking the action bar,
//                   low-health pulse; potion belt with quick keys
//   Path of Exile - buff/debuff bar with timers; bottom XP strip;
//                   item tooltips with equipped-comparison
//   Dragon Warrior- typewriter encounter window ("A slime draws near!")
(() => {
  const MH = window.MH = window.MH || {};
  const $ = id => document.getElementById(id);

  // ================= Aether Sigil =================
  // One circular rune-gauge that replaces the Diablo globes: outer arc = HP,
  // inner arc = MP, and the core is the class's signature resource (glyph +
  // fill + pips). Unique to Misthollow — it reads differently on every class.
  const CLASS_SIGIL = {
    warrior: { g: '⚔', c: '#e05a4a' }, paladin: { g: '☀', c: '#ffe9a8' },
    mage: { g: '✦', c: '#9a8aff' }, necromancer: { g: '☠', c: '#9adba0' },
    cleric: { g: '✚', c: '#cfe2ff' }, thief: { g: '◆', c: '#b8b2c8' },
    assassin: { g: '⌖', c: '#c77dff' }, ranger: { g: '➶', c: '#8ac06a' },
    bard: { g: '♪', c: '#f0b060' },
  };
  const sigil = { hp: { cur: 1, tgt: 1 }, mp: { cur: 1, tgt: 1 }, res: { cur: 0, tgt: 0 },
    cls: 'warrior', resVal: 0, resMax: 0, resName: '', c: null };
  let wavePhase = 0;
  let lastHpSeen = null, hpHitTimer = null;

  // draw a stroked arc gauge: track + filled portion, optional pulse/glow
  function gauge(x, cx, cy, r, w, frac, col, track, glow) {
    const START = Math.PI * 0.75, SWEEP = Math.PI * 1.5;   // 270°, gap at bottom
    x.lineCap = 'round';
    x.lineWidth = w;
    x.strokeStyle = track;
    x.beginPath(); x.arc(cx, cy, r, START, START + SWEEP); x.stroke();
    if (frac > 0.001) {
      if (glow) { x.shadowColor = col; x.shadowBlur = glow; }
      x.strokeStyle = col;
      x.beginPath(); x.arc(cx, cy, r, START, START + SWEEP * Math.max(0, Math.min(1, frac))); x.stroke();
      x.shadowBlur = 0;
    }
  }

  function drawSigil() {
    const c = sigil.c;
    // the sigil is hidden by the r2 HUD (the big HP bar is the one vitals
    // readout); skip the canvas work while it has no layout box
    if (!c || !c.offsetParent) return;
    const x = c.getContext('2d');
    const W = c.width, H = c.height, cx = W / 2, cy = H / 2;
    x.clearRect(0, 0, W, H);
    // ease values toward targets
    sigil.hp.cur += (sigil.hp.tgt - sigil.hp.cur) * 0.08;
    sigil.mp.cur += (sigil.mp.tgt - sigil.mp.cur) * 0.08;
    sigil.res.cur += (sigil.res.tgt - sigil.res.cur) * 0.1;

    // glass disc
    const bg = x.createRadialGradient(cx, cy, 4, cx, cy, W / 2);
    bg.addColorStop(0, 'rgba(14,22,30,0.86)'); bg.addColorStop(1, 'rgba(7,11,16,0.94)');
    x.fillStyle = bg; x.beginPath(); x.arc(cx, cy, W / 2 - 1, 0, 7); x.fill();
    // faint cyan tactical tick rim
    x.strokeStyle = 'rgba(57,197,232,0.5)'; x.lineWidth = 1;
    for (let i = 0; i < 36; i++) {
      const a = i / 36 * Math.PI * 2, r0 = W / 2 - 2.5, r1 = W / 2 - (i % 3 ? 4 : 6);
      x.globalAlpha = i % 3 ? 0.18 : 0.4;
      x.beginPath(); x.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0);
      x.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1); x.stroke();
    }
    x.globalAlpha = 1;

    const sg = CLASS_SIGIL[sigil.cls] || { g: '◆', c: '#39c5e8' };
    // HP outer arc (ember; pulses under 25%)
    const lowHp = sigil.hp.cur < 0.25;
    const pulse = lowHp ? 0.7 + 0.3 * Math.sin(wavePhase * 4) : 1;
    gauge(x, cx, cy, W / 2 - 13, 7, sigil.hp.cur, `rgba(${Math.round(255 * pulse)},${Math.round(90 * pulse)},106,0.95)`,
      'rgba(255,90,106,0.12)', lowHp ? 10 : 0);
    // MP inner arc (indigo)
    gauge(x, cx, cy, W / 2 - 24, 5, sigil.mp.cur, 'rgba(125,140,255,0.95)', 'rgba(125,140,255,0.12)', 0);

    // resource core — class-colored disc filled by the resource fraction
    const coreR = W / 2 - 33;
    x.save();
    x.beginPath(); x.arc(cx, cy, coreR, 0, 7); x.clip();
    x.fillStyle = 'rgba(7,11,16,0.9)'; x.fillRect(0, 0, W, H);
    const cg = x.createRadialGradient(cx, cy + coreR, 1, cx, cy, coreR * 1.6);
    cg.addColorStop(0, sg.c); cg.addColorStop(1, 'rgba(0,0,0,0)');
    x.globalAlpha = 0.18 + 0.5 * sigil.res.cur;   // brighter as the resource builds
    x.fillStyle = cg; x.fillRect(0, 0, W, H);
    x.globalAlpha = 1; x.restore();
    x.strokeStyle = 'rgba(57,197,232,0.35)'; x.lineWidth = 1;
    x.beginPath(); x.arc(cx, cy, coreR, 0, 7); x.stroke();
    // resource pips around the core for small, discrete pools (<=12)
    if (sigil.resMax > 1 && sigil.resMax <= 12) {
      for (let i = 0; i < sigil.resMax; i++) {
        const a = -Math.PI / 2 + i / sigil.resMax * Math.PI * 2;
        const px = cx + Math.cos(a) * (coreR + 3.5), py = cy + Math.sin(a) * (coreR + 3.5);
        x.fillStyle = i < Math.round(sigil.resVal) ? sg.c : 'rgba(120,140,160,0.3)';
        x.beginPath(); x.arc(px, py, 1.6, 0, 7); x.fill();
      }
    }
    // class glyph
    x.fillStyle = sg.c; x.shadowColor = sg.c; x.shadowBlur = 6;
    x.font = `${Math.round(coreR * 0.95)}px serif`;
    x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillText(sg.g, cx, cy - 3);
    x.shadowBlur = 0;
    // resource value (mono)
    if (sigil.resMax > 0) {
      x.fillStyle = '#bfeefb'; x.font = '9px "JetBrains Mono", monospace';
      x.fillText(String(Math.round(sigil.resVal)), cx, cy + coreR * 0.62);
    }
  }

  function globesLoop() {
    wavePhase += 0.045;
    drawSigil();
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
  // shorter hold (gauntlet graphics-01/r4): the encounter line is a beat,
  // not a caption that lingers over the fight
  function dwShow(text, hold = 2600, extend = false) {
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
  let lastDeathAt = 0;
  MH.bus.on('combat.state', on => {
    // the death line's trailing hit text flips combat on for a beat: that is
    // not a new enemy drawing near (gauntlet playability-01/r2)
    // r3: a short beat (1.8s) — the typewriter box sits in the lower arena
    // and was still covering the fight two frames after it began
    if (on && Date.now() - lastDeathAt > 2500) dwShow(`⚔ ${lastFoe ? `${cap(lastFoe)} draws near!` : 'An enemy draws near!'} Command?`, 1800);
  });
  MH.bus.on('mob.death', e => {
    lastDeathAt = Date.now();
    const nm = (e && e.name) || lastFoe || 'the enemy';
    // gauntlet playability-01/r2: the kill is announced by the HUD result
    // line (ui.js, held 7s); the typewriter only speaks when that is absent
    if (MH.feel && MH.feel.result) { const el = $('dw-window'); if (el) { el.classList.remove('show'); dwTarget = ''; } return; }
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
    sigil.c = $('aether-sigil');
    globesLoop();
    window.addEventListener('keydown', e => {
      if (e.key.toLowerCase() === 'q' && !e.ctrlKey && !e.metaKey && !e.shiftKey
          && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) useBelt(0);
    });
    MH.bus.on('map', payload => {
      const p = payload.player;
      if (!p) return;
      sigil.hp.tgt = (p.hp || 0) / Math.max(1, p.max_hp || 1);
      sigil.mp.tgt = (p.mana || 0) / Math.max(1, p.max_mana || 1);
      // glanceable vitals: the big HP bar in the dock carries the state
      // (hurt = amber tint, low = ember pulse) instead of a separate globe
      const hud = $('hud');
      if (hud) {
        hud.classList.toggle('hp-low', sigil.hp.tgt < 0.25);
        hud.classList.toggle('hp-hurt', sigil.hp.tgt >= 0.25 && sigil.hp.tgt < 0.5);
        // gauntlet graphics-02/r2: the bar itself flashes when HP drops so a
        // hit reads on the one big element without hunting the feed
        const hpNow = p.hp || 0;
        // gauntlet playability-01/r1: a pale GHOST of the HP you just lost
        // hangs on the bar for a beat, then drains — the size of the chunk
        // that came off reads on the dock without reading a number
        const hpBar = $('bar-hp');
        let ghost = $('hud-hp-ghost');
        if (hpBar && hpBar.parentNode && !ghost) {
          ghost = document.createElement('div');
          ghost.id = 'hud-hp-ghost';
          hpBar.parentNode.insertBefore(ghost, hpBar);
        }
        if (lastHpSeen != null && hpNow < lastHpSeen) {
          hud.classList.remove('hp-hit'); void hud.offsetWidth; hud.classList.add('hp-hit');
          clearTimeout(hpHitTimer);
          hpHitTimer = setTimeout(() => hud.classList.remove('hp-hit'), 420);
          if (ghost) {
            const maxHp = Math.max(1, p.max_hp || 1);
            ghost.style.transition = 'none';
            ghost.style.width = `${Math.min(100, (lastHpSeen / maxHp) * 100)}%`;
            void ghost.offsetWidth;
            ghost.style.transition = '';
            ghost.style.width = `${(hpNow / maxHp) * 100}%`;
          }
        } else if (ghost) {
          ghost.style.width = `${(hpNow / Math.max(1, p.max_hp || 1)) * 100}%`;
        }
        lastHpSeen = hpNow;
      }
      sigil.cls = String(p.char_class || 'warrior').toLowerCase();
      const r = p.resource;
      if (r && r.max) {
        sigil.res.tgt = Math.max(0, Math.min(1, (r.value || 0) / r.max));
        sigil.resVal = r.value || 0; sigil.resMax = r.max; sigil.resName = r.name || '';
      } else { sigil.res.tgt = 0; sigil.resVal = 0; sigil.resMax = 0; sigil.resName = ''; }
      renderBelt();
      renderBuffs();
      renderXpStrip(p);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
