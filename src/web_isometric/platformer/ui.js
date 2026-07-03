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

  // ---- accessibility / UI preferences (persisted) ----
  MH.prefs = {
    textSize: lsGet('mh_text_size') || 'normal',          // normal | large | huge
    highContrast: lsGet('mh_high_contrast') === '1',
    dmgNumbers: lsGet('mh_dmg_numbers') !== '0',          // floating combat numbers, default on
  };
  function applyPrefs() {
    const b = document.body;
    if (!b) return;
    b.classList.toggle('uitext-large', MH.prefs.textSize === 'large');
    b.classList.toggle('uitext-huge', MH.prefs.textSize === 'huge');
    b.classList.toggle('hicontrast', !!MH.prefs.highContrast);
  }
  applyPrefs();

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

  // Skills that are passive/automatic or pure utility — they do nothing when
  // "used", so they never belong on the action bar (the player can still bind
  // them by hand). Everything else in a class roster is an active ability.
  const NON_HOTBAR_SKILLS = new Set([
    'parry', 'dodge', 'shield_block', 'second_attack', 'third_attack', 'fourth_attack',
    'evasion', 'dual_wield', 'enhanced_damage', 'sixth_sense', 'sneak', 'hide',
    'track', 'scan', 'detect_traps', 'lore', 'scribe', 'doctrine', 'swear', 'evolve',
    'oath', 'tame', 'steal', 'pick_lock',
  ]);
  // Curated "open with these" order per class — the iconic actives a new player
  // should have ready. These are only an ordering hint: every id is validated
  // against the live roster (spells/skills) before it is bound, so a class only
  // ever gets abilities it actually has.
  const CLASS_KIT_ORDER = {
    warrior:     ['bash', 'cleave', 'kick', 'execute', 'rally', 'rescue', 'charge'],
    paladin:     ['censure', 'order_verdict', 'holy_smite', 'absolution', 'halo_of_reckoning', 'turn_undead', 'rescue', 'bash'],
    ranger:      ['truesight_shot', 'wildbond_strike', 'loosing_storm', 'quarry_mark', 'call_lightning'],
    thief:       ['backstab', 'circle', 'trip', 'low_blow', 'pocket_sand', 'jackpot'],
    assassin:    ['backstab', 'mark', 'expose', 'vital', 'feint', 'execute_contract', 'fade'],
    mage:        ['magic_missile', 'fireball', 'lightning_bolt', 'chill_touch', 'sleep', 'towerbolt'],
    necromancer: ['soul_bolt', 'chill_touch', 'soul_siphon', 'animate_dead', 'soul_reap'],
    cleric:      ['holy_smite', 'cure_light', 'heal', 'turn_undead', 'bless', 'flamestrike'],
    bard:        ['mockery', 'fascinate', 'crescendo', 'discordant_note', 'sleep'],
  };

  // turn an ability id into the command form the MUD expects, resolving whether
  // it is a spell (needs `cast '...'`) or a skill (sent as the bare command;
  // the server recombines multi-word skills like "shadow dance")
  function abilityCommand(id, spellSet) {
    const name = String(id || '');
    if (spellSet.has(name)) return `cast '${name.replace(/_/g, ' ')}'`;
    return name.replace(/_/g, ' ');
  }

  // WoW-style quality of life: the first time a character logs in, lay their
  // basic class kit AND any active talents they have learned onto the empty
  // action-bar slots — de-noised (no passives) and class-ordered.
  let autofilled = false;
  function autofillBar() {
    const pdata = MH.state.player;
    if (autofilled || !pdata || !pdata.char_class) return;
    autofilled = true;
    const fillKey = `misthollow_bar_filled_${(pdata.name || '').toLowerCase()}`;
    if (lsGet(fillKey)) return;

    const cls = String(pdata.char_class || '').toLowerCase();
    const spells = pdata.class_spells || [];
    const spellSet = new Set(spells);
    const rosterSkills = pdata.class_skills || [];
    const rosterSet = new Set(rosterSkills);
    const learned = pdata.skills || {};   // includes talent-granted actives once learned
    const isActiveSkill = id => id && !NON_HOTBAR_SKILLS.has(id);

    const seen = new Set();
    const collect = (list, ids) => {
      for (const id of ids) {
        if (!id) continue;
        const command = abilityCommand(id, spellSet);
        const key = command.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key); list.push(command);
      }
    };

    // basics = curated class kit (validated against the roster), then the rest
    // of the roster's actives so nothing useful is left behind
    const basics = [];
    collect(basics, (CLASS_KIT_ORDER[cls] || []).filter(id => spellSet.has(id) || (rosterSet.has(id) && isActiveSkill(id))));
    collect(basics, spells);
    collect(basics, rosterSkills.filter(isActiveSkill));
    // talents / trained extras: active abilities the player has actually learned
    // that the class roster didn't list (e.g. Shadow Dance from a talent)
    const talents = [];
    collect(talents, Object.keys(learned).filter(id => !rosterSet.has(id) && !spellSet.has(id) && isActiveSkill(id)));

    // interleave so learned talents always get a couple of slots even when the
    // basic kit alone would fill the bar
    const freeCount = hotbar.filter(s => !s).length;
    const reserve = Math.min(talents.length, 2);
    const basicHead = Math.max(0, freeCount - reserve);
    const cmds = basics.slice(0, basicHead)
      .concat(talents.slice(0, reserve))
      .concat(basics.slice(basicHead))
      .concat(talents.slice(reserve));

    let changed = false;
    for (let i = 0; i < BAR_SIZE && cmds.length; i++) {
      if (!hotbar[i]) { hotbar[i] = cmds.shift(); changed = true; }
    }
    if (changed) {
      lsSet(HOTBAR_KEY, JSON.stringify(hotbar));
      lsSet(fillKey, '1');
      renderHotbar();
      flash('Your class abilities are on the action bar — drag from K to customize.');
    }
  }

  function bindSlot(i, cmd) {
    hotbar[i] = String(cmd || '').trim();
    lsSet(HOTBAR_KEY, JSON.stringify(hotbar));
    renderHotbar();
  }
  // bind a command to the first free action-bar slot; returns false if full or
  // already bound. Used by the spellbook / doctrine "⊕ Bar" buttons.
  function bindToHotbar(cmd) {
    const c = String(cmd || '').trim();
    if (!c) return false;
    if (hotbar.some(s => (s || '').toLowerCase() === c.toLowerCase())) return false;
    const free = hotbar.findIndex(s => !s);
    if (free < 0) return false;
    bindSlot(free, c);
    return true;
  }

  // spell mana costs (static), fetched once after login
  let abilityCosts = {};
  function costForCmd(cmd) {
    const m = String(cmd || '').match(/^cast '([^']+)'$/);
    if (!m) return null;
    const a = abilityCosts[m[1].replace(/ /g, '_')];
    return a ? a.mana_cost : null;
  }
  function loadAbilityCosts() {
    if (!MH.state.playerName) return;
    fetch(`/abilities?player=${encodeURIComponent(MH.state.playerName)}`)
      .then(r => r.json()).then(d => { abilityCosts = d.abilities || {}; renderHotbar(); }).catch(() => {});
  }
  function updateHotbarAffordability() {
    const mana = (MH.state.player && MH.state.player.mana) || 0;
    els.hotbar.querySelectorAll('.hotslot').forEach(slot => {
      const cost = Number(slot.dataset.cost || 0);
      slot.classList.toggle('unaffordable', cost > 0 && mana < cost);
    });
  }

  // styled hover tooltip for hotbar slots — name, cost, cooldown, key, mastery
  function showHotbarTip(e, cmd, i, prof, cost) {
    const tip = document.getElementById('hotbar-tip');
    if (!tip) return;
    if (!cmd) {
      tip.innerHTML = `<div class="ht-name">Empty slot</div>`
        + `<div class="ht-key">drag a skill here from K, or right-click to bind</div>`;
    } else {
      const name = String(cmd).replace(/^cast '/, '').replace(/'$/, '').replace(/_/g, ' ');
      const skillName = String(cmd).replace(/^cast '/, '').replace(/'$/, '').replace(/ /g, '_');
      const a = abilityCosts[skillName] || {};
      const meta = [];
      if (cost) meta.push(`<b>${cost}</b> mana`);
      if (a.cooldown) meta.push(`⏳ ${a.cooldown}s cd`);
      if (prof != null) meta.push(`${prof}% mastery`);
      tip.innerHTML = `<div class="ht-name">${name.replace(/\b\w/g, c => c.toUpperCase())}</div>`
        + (meta.length ? `<div class="ht-meta">${meta.join(' · ')}</div>` : '')
        + `<div class="ht-key">press <b>${(i + 1) % 10}</b> · right-click to rebind</div>`;
    }
    tip.classList.add('show');
    positionHotbarTip(e);
  }
  function positionHotbarTip(e) {
    const tip = document.getElementById('hotbar-tip');
    if (!tip || !tip.classList.contains('show')) return;
    const r = tip.getBoundingClientRect();
    tip.style.left = Math.max(6, Math.min(e.clientX - r.width / 2, window.innerWidth - r.width - 6)) + 'px';
    tip.style.top = Math.max(6, e.clientY - r.height - 14) + 'px';
  }
  function hideHotbarTip() {
    const tip = document.getElementById('hotbar-tip');
    if (tip) tip.classList.remove('show');
  }

  function renderHotbar() {
    els.hotbar.innerHTML = '';
    const skills = (MH.state.player && MH.state.player.skills) || {};
    hotbar.forEach((cmd, i) => {
      const slot = document.createElement('div');
      slot.className = 'hotslot';
      const skillName = String(cmd || '').replace(/^cast '/, '').replace(/'$/, '');
      const prof = skills[skillName];
      const cost = costForCmd(cmd);
      if (cost != null) slot.dataset.cost = cost;
      slot.setAttribute('draggable', 'true');
      slot.innerHTML = `<span class="key">${(i + 1) % 10}</span>`
        + (prof != null ? `<span class="prof">${prof}%</span>` : '')
        + (cost ? `<span class="cost">${cost}</span>` : '')
        + `<canvas width="20" height="20"></canvas>`
        + `<span class="lbl">${cmd || '—'}</span><div class="cd"></div>`;
      drawIcon(slot.querySelector('canvas'), iconKindFor(cmd));
      slot.addEventListener('mouseenter', e => showHotbarTip(e, cmd, i, prof, cost));
      slot.addEventListener('mousemove', e => positionHotbarTip(e));
      slot.addEventListener('mouseleave', hideHotbarTip);
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
    updateHotbarAffordability();
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

  // Free-text command box: run ANY typed command and surface its reply in a
  // readable card, so the ~400 info/utility/social commands that otherwise
  // dump silently into the hidden terminal drawer actually show a result.
  // Commands whose effect is already visible (movement, combat engage, chat,
  // posture) just send raw so we don't pop a redundant card over them.
  const TYPED_SILENT = new Set(['n', 's', 'e', 'w', 'u', 'd', 'ne', 'nw', 'se', 'sw',
    'north', 'south', 'east', 'west', 'up', 'down', 'northeast', 'northwest', 'southeast', 'southwest',
    'enter', 'leave', 'recall', 'travel', 'flee', 'escape', 'disengage', 'retreat',
    'kill', 'attack', 'k', 'att', 'murder', 'say', 'tell', 'reply', 'whisper', 'gossip', 'gos',
    'shout', 'yell', 'holler', 'chat', 'gt', 'gtell', 'qsay', 'grats', 'me', 'emote',
    'sit', 'stand', 'sleep', 'rest', 'wake']);
  async function runTypedCommand(raw) {
    const cmd = String(raw || '').trim();
    if (!cmd) return;
    const first = cmd.split(/\s+/)[0].toLowerCase();
    if (/^['":]/.test(cmd) || TYPED_SILENT.has(first)) { MH.sendCommand(cmd); return; }
    const p = captureOutput(1300);
    MH.sendCommand(cmd);
    let lines = [];
    try { lines = await p; } catch (_) {}
    const clean = ((MH.cleanInfoText ? MH.cleanInfoText(lines.join('\n'), cmd) : lines.join('\n')) || '').trim();
    if (clean && MH.immersion && MH.immersion.showDetailCard) MH.immersion.showDetailCard(cmd, clean, 'detail');
    else if (clean) flash(clean.split('\n')[0].slice(0, 110));
  }

  // ---- combat rhythm + input gating ----------------------------------------
  // The server resolves combat in fixed ~4s rounds and already enforces ability
  // cooldowns; this mirrors that on the client so the basic attack can't be
  // spammed and every action reads against a clear rhythm. Purely a feel layer.
  MH.combat = {
    roundMs: 4000,            // server combat round (main.py: combat_tick every 4s)
    roundStart: 0,            // performance.now() of the last round push
    gcdMs: 1000,              // shared global cooldown so two actions can't fire at once
    gcd: { until: 0, dur: 1000 },
    cd: {},                   // skill -> { until, dur } (ms, performance.now timebase)
    FLEE_CD: { flee: 6000, escape: 8000, disengage: 6000, retreat: 6000 },
    skillOf(cmd) {
      const c = String(cmd || '').trim().toLowerCase();
      const m = c.match(/^cast '([^']+)'/);
      if (m) return m[1].replace(/ /g, '_');
      return c.split(/\s+/)[0] || '';
    },
    // full underscore key (e.g. "shadow dance" -> "shadow_dance") to match the
    // server's cooldown attribute names; skillOf only keeps the first word
    cdKey(cmd) {
      const c = String(cmd || '').trim().toLowerCase();
      const m = c.match(/^cast '([^']+)'/);
      if (m) return m[1].replace(/ /g, '_');
      return c.replace(/\s+/g, '_');
    },
    // the active cooldown entry for a slot, matching either the full key (server
    // cooldowns) or the first-word key (client-predicted spell/flee cooldowns)
    cdEntry(cmd) { return this.cd[this.cdKey(cmd)] || this.cd[this.skillOf(cmd)]; },
    // fold the server's authoritative cooldowns (seconds remaining) into the
    // single cd map so the action bar paints skill cooldowns — not just spells —
    // for every class. Keeps the original duration across refreshes for a
    // correct sweep, and counts down smoothly between the 4s round pushes.
    syncServerCooldowns(cds) {
      if (!cds) return;
      const now = performance.now();
      for (const k in cds) {
        const secs = cds[k];
        if (!(secs > 0)) continue;
        const ms = secs * 1000, until = now + ms;
        const ex = this.cd[k];
        const dur = (ex && ex.until > now && ex.dur >= ms) ? ex.dur : ms;
        this.cd[k] = { until, dur };
      }
    },
    // is this a combat action that should be gated/rhythm-bound?
    isCombatCmd(cmd) {
      const s = this.skillOf(cmd);
      if (['attack', 'kill', 'cast'].includes(s)) return true;
      if (this.FLEE_CD[s] != null) return true;
      return !!(abilityCosts[s] || /^cast '/.test(String(cmd || '')));
    },
    // gate duration (ms) this command should impose on its own slot
    cdFor(cmd) {
      const s = this.skillOf(cmd);
      if (this.FLEE_CD[s] != null) return this.FLEE_CD[s];
      const a = abilityCosts[s];
      if (a && a.cooldown) return a.cooldown * 1000;
      return 0;   // basic attack / cast with no listed cd -> shared GCD only
    },
    ready(cmd) {
      const now = performance.now();
      if (now < this.gcd.until) return false;
      const e = this.cdEntry(cmd);
      if (e && now < e.until) return false;
      return true;
    },
    trigger(cmd) {
      const now = performance.now();
      this.gcd = { until: now + this.gcdMs, dur: this.gcdMs };
      const cdms = this.cdFor(cmd);
      if (cdms > 0) this.cd[this.skillOf(cmd)] = { until: now + cdms, dur: cdms };
    },
    noteRound() { this.roundStart = performance.now(); },
    roundFrac() {
      if (!this.roundStart) return 0;
      return Math.max(0, Math.min(1, (performance.now() - this.roundStart) / this.roundMs));
    },
  };

  function useHotbar(i) {
    const cmd = hotbar[i];
    if (!cmd) return;
    const slot = els.hotbar.children[i];
    // gate combat actions to the round / cooldowns (the attack slot is handled
    // by the scene's engage logic, so it bypasses the hard block here)
    if (MH.combat.isCombatCmd(cmd) && MH.combat.skillOf(cmd) !== 'attack'
        && MH.combat.skillOf(cmd) !== 'kill' && !MH.combat.ready(cmd)) {
      flashNotReady(slot);
      return;
    }
    if (MH.sfx) MH.sfx.ui();
    // slots map to real UI where possible - commands shouldn't vanish into
    // the void
    if (cmd === 'attack' || cmd === 'kill') {
      // delegate to the scene: it engages once, then the server auto-swings each
      // round; mashing while already engaged is a no-op (gated there)
      MH.bus.emit('player.attack');
    } else if (cmd === 'inventory' || cmd === 'equipment') {
      renderInventory(); openModal('modal-inv');
    } else if (cmd === 'quests' || cmd === 'journal') {
      openJournal();
    } else if (cmd === 'score') {
      openScore();
    } else if (cmd === 'look') {
      if (lastRoomShown) showRoom(lastRoomShown.room, lastRoomShown.zoneName);
      commandWithPeek('look');
    } else if (/^cast '[^']+'$/.test(cmd)) {
      const spell = (cmd.match(/^cast '([^']+)'$/) || [])[1] || '';
      const cost = costForCmd(cmd);
      if (cost != null && ((MH.state.player && MH.state.player.mana) || 0) < cost) {
        flash(`Not enough mana — ${spell} needs ${cost}`);
        try { tone({ f: 160, f2: 110, type: 'sine', dur: 0.12, vol: 0.05 }); } catch (_) {}
        return;
      }
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
    // record the GCD / ability cooldown for non-attack combat actions; the
    // attack slot's rhythm is triggered by the scene's engage logic, and the
    // tick loop (tickHotbarCooldowns) drives all slot overlays from MH.combat
    const s = MH.combat.skillOf(cmd);
    if (MH.combat.isCombatCmd(cmd) && s !== 'attack' && s !== 'kill') MH.combat.trigger(cmd);
  }
  // brief "not ready" shake so an eaten press is acknowledged
  function flashNotReady(slot) {
    if (!slot) return;
    if (MH.sfx) { try { tone({ f: 150, f2: 120, type: 'sine', dur: 0.08, vol: 0.04 }); } catch (_) {} }
    slot.classList.remove('notready');
    void slot.offsetWidth;
    slot.classList.add('notready');
  }
  // Continuously paint each hotbar slot's cooldown/round overlay from the single
  // source of truth (MH.combat), so visuals stay correct no matter what fired
  // the action (hotbar, scene attack, or a server round push).
  function tickHotbarCooldowns() {
    if (!els.hotbar) return;
    const now = performance.now();
    const inCombat = !!(MH.state && MH.state.inCombat);
    hotbar.forEach((cmd, i) => {
      const slot = els.hotbar.children[i];
      if (!slot) return;
      const cd = slot.querySelector('.cd');
      if (!cd) return;
      const s = MH.combat.skillOf(cmd);
      const isAtk = s === 'attack' || s === 'kill';
      let frac = 0, num = 0;
      // basic attack: show the round rhythm while engaged (informational, not a lock)
      if (isAtk && inCombat) { frac = 1 - MH.combat.roundFrac(); slot.classList.add('engaged'); }
      else slot.classList.remove('engaged');
      // real ability / flee cooldown -> hard lock + numeral
      const e = MH.combat.cdEntry(cmd);
      let locked = false;
      if (e && now < e.until) {
        const rem = e.until - now;
        frac = Math.max(frac, rem / e.dur);
        num = Math.ceil(rem / 1000);
        locked = true;
      } else if (!isAtk && MH.combat.isCombatCmd(cmd) && now < MH.combat.gcd.until) {
        // shared GCD wipe on the other combat slots
        frac = Math.max(frac, (MH.combat.gcd.until - now) / MH.combat.gcd.dur);
        locked = true;
      }
      slot.classList.toggle('disabled', locked);
      if (frac > 0.001) { cd.style.opacity = '1'; cd.style.setProperty('--cd-ang', (frac * 360) + 'deg'); }
      else { cd.style.opacity = '0'; }
      let nEl = slot.querySelector('.cd-num');
      if (num >= 1) {
        if (!nEl) { nEl = document.createElement('span'); nEl.className = 'cd-num'; slot.appendChild(nEl); }
        nEl.textContent = num; nEl.style.display = 'flex';
      } else if (nEl) { nEl.style.display = 'none'; }
    });
  }

  // (cooldown/round overlays are painted continuously by tickHotbarCooldowns
  // from MH.combat, the single source of truth — no per-press animation needed)

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
    updateCrest(player);
  }

  // top-bar crest: name + class·level + a round head-and-shoulders portrait
  function updateCrest(p) {
    if (!p) return;
    const nm = document.getElementById('crest-name'), sub = document.getElementById('crest-sub');
    if (nm) nm.textContent = `${p.name || ''}${p.title ? ' ' + p.title : ''}`;
    if (sub) sub.textContent = `${p.char_class || ''} · LV ${p.level || 1}`;
    const c = document.getElementById('crest-portrait');
    if (!c || !window.MH || !MH.game) return;
    try {
      const scene = MH.game.scene.getScenes(true)[0];
      const texKey = MH.tdSprites.playerKey((p.char_class || '').toLowerCase());
      const tex = scene.textures.get(scene.textures.exists(texKey) ? texKey : 'td_player_warrior');
      const f = tex.get('d0');
      const ctx = c.getContext('2d');
      ctx.clearRect(0, 0, c.width, c.height);
      ctx.imageSmoothingEnabled = false;
      // crop the head + shoulders (top ~70% of the frame) into the round chip
      ctx.drawImage(tex.getSourceImage(), f.cutX, f.cutY, f.cutWidth, f.cutHeight * 0.7, 2, 2, c.width - 4, c.height - 4);
    } catch (_) { /* textures not ready yet */ }
  }

  // right-side CONTACTS: everyone in the room with disposition, level, HP, and
  // a target/interact action — mirrors the Aether Grid spec
  function renderContacts(payload) {
    const host = document.getElementById('ct-list'), panel = document.getElementById('contacts');
    if (!host || !panel) return;
    const p = (payload && payload.player) || MH.state.player || {};
    const room = ((payload && payload.rooms) || []).find(r => r.vnum === p.vnum);
    const list = [];
    ((room && room.mobs) || []).forEach(m => list.push({
      name: m.name, level: m.level, hp: m.hp, maxHp: m.maxHp, hostile: !!m.hostile,
      kind: m.hostile ? 'hostile' : (m.shopkeeper || m.trainer || m.quest ? 'friendly' : 'neutral'),
    }));
    ((room && room.players) || []).forEach(pl => {
      const nm = typeof pl === 'string' ? pl : (pl && pl.name);
      if (nm && nm !== p.name) list.push({ name: nm, level: (pl && pl.level) || '', kind: 'friendly', player: true });
    });
    const cc = document.getElementById('ct-count');
    if (cc) cc.textContent = list.length;
    panel.classList.toggle('empty', list.length === 0);
    host.innerHTML = '';
    const tgt = currentTarget && currentTarget.name;
    for (const e of list) {
      const row = document.createElement('div');
      row.className = 'ct-row' + (e.kind === 'friendly' ? ' friendly' : '') + (tgt && tgt === e.name ? ' target' : '');
      const pct = e.maxHp ? Math.max(0, Math.min(100, ((e.hp != null ? e.hp : e.maxHp) / e.maxHp) * 100)) : 100;
      const initial = String(e.name || '?').replace(/^(a|an|the)\s+/i, '').charAt(0).toUpperCase();
      row.innerHTML = `<div class="ct-dot ${e.kind}">${initial}</div>`
        + `<div class="ct-meta"><div class="ct-nm">${e.name}</div><div class="ct-lv">LV ${e.level || '?'}</div>`
        + (e.maxHp ? `<div class="ct-hp"><i style="width:${pct}%"></i></div>` : '') + `</div>`
        + `<div class="ct-act" title="${e.hostile ? 'attack' : 'interact'}"><span>${e.hostile ? '⚔' : '◆'}</span></div>`;
      const target = () => { const sc = MH.game && MH.game.scene.getScenes(true).find(s => s.targetByName); if (sc) sc.targetByName(e.name); };
      row.addEventListener('click', target);
      const act = row.querySelector('.ct-act');
      if (act) act.addEventListener('click', ev => {
        ev.stopPropagation(); target();
        if (e.hostile) MH.sendCommand('kill ' + MH.mobKeyword(e.name));
        else if (!e.player) MH.bus.emit('npc.talk', { name: e.name, quest: '' });
      });
      host.appendChild(row);
    }
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
  // consider/threat by level delta — the classic "is this safe?" read
  function threatFor(mobLevel) {
    const pl = (MH.state.player && MH.state.player.level) || 1;
    const d = (mobLevel || pl) - pl;
    if (d <= -8) return { txt: 'trivial', col: '#6a7084' };
    if (d <= -4) return { txt: 'easy', col: '#6fd685' };
    if (d <= -2) return { txt: 'manageable', col: '#9adba0' };
    if (d <= 1) return { txt: 'even', col: '#e8c168' };
    if (d <= 3) return { txt: 'tough', col: '#e0a07a' };
    if (d <= 6) return { txt: 'dangerous', col: '#e0563a' };
    return { txt: 'DEADLY', col: '#ff5a7a' };
  }
  let currentTarget = null;
  function setTarget(data) {
    const prev = currentTarget;
    currentTarget = data;
    if (!data) { els.targetFrame.classList.remove('show'); return; }
    els.targetFrame.classList.add('show');
    els.targetFrame.classList.toggle('friendly', !data.hostile && !data.fighting);
    const th = threatFor(data.level);
    els.targetName.innerHTML = `<span class="tf-nm">${data.name}</span>`
      + `<span class="tf-tag" style="color:${th.col}">LV ${data.level || '?'} · ${th.txt}</span>`;
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

  // One-time contextual teaching: the first time a new mechanic appears on
  // screen, say ONE sentence about it (then never again — stored per browser).
  function teach(key, msg) {
    try {
      if (lsGet('mh_tip_' + key)) return;
      lsSet('mh_tip_' + key, '1');
    } catch (_) { return; }
    flash(msg);
    if (typeof clogLineRef === 'function') clogLineRef(`💡 ${msg}`, 'info');
  }
  let clogLineRef = null;   // bound once the feed exists

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
  function toast(title, body, kind, onClick) {
    let host = document.getElementById('toast-host');
    if (!host) { host = document.createElement('div'); host.id = 'toast-host'; document.body.appendChild(host); }
    const t = document.createElement('div');
    t.className = 'mh-toast ' + (kind || '');
    t.innerHTML = `<div class="tt-t">${title}</div><div class="tt-b">${body}</div>`;
    if (onClick) {
      t.style.cursor = 'pointer';
      t.addEventListener('click', () => { onClick(); t.classList.remove('in'); setTimeout(() => t.remove(), 400); });
    }
    host.appendChild(t);
    requestAnimationFrame(() => t.classList.add('in'));
    setTimeout(() => { t.classList.remove('in'); setTimeout(() => t.remove(), 400); }, 5200);
  }

  // cinematic level-up: a full-screen golden burst with rays + the new level.
  // The scene also plays an in-world pillar; this is the can't-miss UI moment.
  let _luTimer = null;
  function cinematicLevelUp() {
    const ov = document.getElementById('levelup');
    if (!ov) return;
    const lvlEl = document.getElementById('lu-level');
    const setLvl = () => { const l = MH.state.player && MH.state.player.level; if (lvlEl) lvlEl.textContent = l ? `LEVEL ${l}` : ''; };
    setLvl();
    // the new level usually arrives a beat later via state refresh
    setTimeout(setLvl, 500);
    setTimeout(setLvl, 1100);
    ov.classList.remove('show');
    void ov.offsetWidth;            // restart the CSS animation
    ov.classList.add('show');
    clearTimeout(_luTimer);
    _luTimer = setTimeout(() => ov.classList.remove('show'), 2700);
  }

  // brief sparkle on the action-bar slot whose skill just improved/evolved
  function sparkleHotbarSkill(skill) {
    if (!els.hotbar) return;
    const key = String(skill || '').toLowerCase().replace(/ /g, '_');
    [...els.hotbar.children].forEach((slot, i) => {
      const cmd = String(hotbar[i] || '').toLowerCase().replace(/^cast '/, '').replace(/'$/, '').replace(/ /g, '_');
      if (cmd && (cmd === key || cmd.includes(key) || key.includes(cmd))) {
        slot.classList.remove('skillup'); void slot.offsetWidth; slot.classList.add('skillup');
        setTimeout(() => slot.classList.remove('skillup'), 1400);
      }
    });
  }
  // cinematic banner when a warrior ability evolves into its next form
  let _evoTimer = null;
  function cinematicEvolve(ability, evolution) {
    let host = document.getElementById('evolve-banner');
    if (!host) { host = document.createElement('div'); host.id = 'evolve-banner'; document.body.appendChild(host); }
    host.innerHTML = `<div class="evo-rays"></div><div class="evo-card">`
      + `<div class="evo-h">★ ABILITY EVOLVED ★</div>`
      + `<div class="evo-name">${String(ability).toUpperCase()} <span>→</span> ${evolution}</div></div>`;
    host.classList.remove('show'); void host.offsetWidth; host.classList.add('show');
    clearTimeout(_evoTimer);
    _evoTimer = setTimeout(() => host.classList.remove('show'), 3400);
    if (MH.sfx && MH.sfx.level) MH.sfx.level();
    sparkleHotbarSkill(ability);
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
  // opening a panel from the UI also issues the matching MUD command(s), so
  // beginner quests that ask you to "type score / inventory / skills" count
  // whether you type them or click the buttons. Sent silently (raw feed only).
  const MODAL_CMDS = {
    'modal-inv': ['inventory', 'equipment'],
    'modal-score': ['score'],
    'modal-spells': ['skills', 'spells'],
    'modal-journal': ['quests'],
    'modal-shop': ['list'],
  };
  // ---- draggable panels (modals + combat log) ----
  // Headers become drag handles; position is converted to explicit left/top
  // (overriding any !important corner anchoring) and persisted per-panel so a
  // reopened panel stays where the player parked it.
  const DRAG_POS = {};
  function makeDraggable(el, handle) {
    if (!el || !handle || handle.dataset.drag) return;
    handle.dataset.drag = '1';
    handle.style.cursor = 'move';
    handle.style.userSelect = 'none';
    const stage = () => el.offsetParent || document.getElementById('game-root') || document.body;
    // restore a saved position when the panel becomes visible
    const applySaved = () => {
      const p = DRAG_POS[el.id];
      if (!p) return;
      el.classList.add('dragged');
      el.style.setProperty('left', p.x + 'px', 'important');
      el.style.setProperty('top', p.y + 'px', 'important');
      el.style.setProperty('right', 'auto', 'important');
      el.style.setProperty('bottom', 'auto', 'important');
      el.style.setProperty('transform', 'none', 'important');
    };
    el._restoreDrag = applySaved;
    handle.addEventListener('pointerdown', e => {
      // let the close button, tools and any control inside the header work
      if (e.target.closest('.x, .clog-tools, button, input, select, textarea, [data-close], [data-tab], a, .foe-row')) return;
      if (e.button !== 0) return;
      const r = el.getBoundingClientRect();
      const sr = stage().getBoundingClientRect();
      const offX = e.clientX - r.left, offY = e.clientY - r.top;
      el.classList.add('dragged');
      el.style.setProperty('transform', 'none', 'important');
      el.style.setProperty('right', 'auto', 'important');
      el.style.setProperty('bottom', 'auto', 'important');
      const move = ev => {
        let x = ev.clientX - sr.left - offX;
        let y = ev.clientY - sr.top - offY;
        x = Math.max(2, Math.min(x, sr.width - r.width - 2));
        y = Math.max(2, Math.min(y, sr.height - r.height - 2));
        el.style.setProperty('left', x + 'px', 'important');
        el.style.setProperty('top', y + 'px', 'important');
        DRAG_POS[el.id] = { x, y };
      };
      const up = () => {
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', up);
        document.body.style.cursor = '';
      };
      document.body.style.cursor = 'move';
      window.addEventListener('pointermove', move);
      window.addEventListener('pointerup', up);
      e.preventDefault();
    });
  }
  function setupDraggables() {
    document.querySelectorAll('.modal').forEach(m => {
      const h = m.querySelector('.modal-head');
      if (h) makeDraggable(m, h);
    });
    const cl = document.getElementById('combat-log');
    if (cl) {
      makeDraggable(cl, cl.querySelector('.head'));
      // remember the player's chosen feed height across reloads (v2: the feed
      // moved to a bottom ticker strip, so stale v1 sizes must not apply)
      try {
        const saved = JSON.parse(lsGet('mh_clog_size2') || 'null');
        if (saved && saved.h) cl.style.height = saved.h + 'px';
        if (window.ResizeObserver) {
          let t = null;
          new ResizeObserver(() => {
            if (cl.classList.contains('collapsed')) return;
            clearTimeout(t);
            t = setTimeout(() => lsSet('mh_clog_size2', JSON.stringify({ h: Math.round(cl.offsetHeight) })), 300);
          }).observe(cl);
        }
      } catch (_) {}
    }
    const chat = document.getElementById('chat-panel');
    if (chat) { const ch = chat.querySelector('#chat-tabs, .chat-head, .head'); if (ch) makeDraggable(chat, ch); }
    // the combat "what you're fighting" boxes drag by their whole body
    const duel = document.getElementById('duel-card');
    if (duel) makeDraggable(duel, duel);
    const tf = document.getElementById('target-frame');
    if (tf) makeDraggable(tf, tf);
  }

  function openModal(id) {
    const already = anyModalOpen();
    closeModals(true);
    $(id).classList.add('open');
    const bd = $('modal-backdrop');
    if (bd) bd.classList.add('show');
    setWorldInput(false);
    if (MH.sfx) MH.sfx.ui();
    (MODAL_CMDS[id] || []).forEach(c => { try { MH.sendCommand(c, false); } catch (_) {} });
  }
  function closeModals(silent) {
    const had = anyModalOpen();
    document.querySelectorAll('.modal.open').forEach(m => {
      // play the open animation in reverse for a soft close
      m.classList.add('closing');
      setTimeout(() => m.classList.remove('closing'), 160);
      m.classList.remove('open');
    });
    const bd = $('modal-backdrop');
    if (bd) bd.classList.remove('show');
    setWorldInput(true);
    if (had && !silent && MH.sfx) MH.sfx.uiBack();
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
      const scene = MH.game.scene.getScenes(true).find(s => s.layout) || MH.game.scene.getScenes(true)[0];
      // Prefer the real LPC paperdoll (matches the in-world character + gear).
      if (MH.lpc && MH.lpc.isReady()) {
        const spec = { char_class: p.char_class, sex: p.sex || 'male', equipment: p.equipment || {} };
        MH.lpc.drawPortrait(scene, spec, canvas);
        return;
      }
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
    const badge = item ? itemStatBadge(item) : '';
    // equipped items show their stat in place of the slot label
    const label = badge ? `<span class="pd-slotname pd-statlabel">${badge}</span>` : `<span class="pd-slotname">${slot}</span>`;
    return `<div class="pd-socket${filled}" data-slot="${slot}" ${item ? `data-name="${item.name}" data-cmd="remove ${MH.mobKeyword(item.name)}"` : ''} title="${item ? item.name + ' (click to remove)' : slot}">`
      + `<canvas width="34" height="34"></canvas>${label}`
      + `${item && rar !== 'common' ? `<i class="pd-rar ${rar}"></i>` : ''}</div>`;
  }
  let invFilter = '', invSort = 'slot';
  // ---- item hover tooltip (inventory & equipment) ----
  const STAT_NAMES = {
    hitroll: 'Hit Roll', hit: 'Hit Roll', damroll: 'Damage', dam: 'Damage', ac: 'Armor Class',
    armor: 'Armor', str: 'Strength', strength: 'Strength', int: 'Intelligence', intelligence: 'Intelligence',
    wis: 'Wisdom', wisdom: 'Wisdom', dex: 'Dexterity', dexterity: 'Dexterity', con: 'Constitution',
    constitution: 'Constitution', cha: 'Charisma', charisma: 'Charisma', hp: 'Health', max_hp: 'Health',
    mana: 'Mana', max_mana: 'Mana', mv: 'Moves', move: 'Moves', moves: 'Moves', saves: 'Saving Throws',
    save: 'Saving Throws', age: 'Age',
  };
  const prettyStat = t => STAT_NAMES[String(t).toLowerCase()] || String(t).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  // average damage of a dice string like "2d6+1"
  function diceAvg(d) {
    const m = /(\d+)\s*d\s*(\d+)(?:\s*\+\s*(\d+))?/i.exec(String(d || ''));
    if (!m) return 0;
    return Math.round((Number(m[1]) * (Number(m[2]) + 1) / 2 + (m[3] ? Number(m[3]) : 0)) * 10) / 10;
  }
  // flatten an item's combat-relevant numbers into { statName: total }
  function itemStatTotals(item) {
    const m = {};
    if (!item) return m;
    const add = (k, v) => { if (v) m[k] = (m[k] || 0) + Number(v); };
    if (item.armor) add('Armor', item.armor);
    if (item.damage_dice) add('Avg Dmg', diceAvg(item.damage_dice));
    (item.affects || []).forEach(a => {
      const t = a.type != null ? a.type : (a.location != null ? a.location : (a.applies_to != null ? a.applies_to : a.stat));
      const v = a.value != null ? a.value : a.modifier;
      if (t != null && t !== '' && v != null) add(prettyStat(t), v);
    });
    return m;
  }
  // map an inventory item to the right verb: weapons are wielded, consumables
  // and devices are used (cmd_use dispatches quaff/recite/zap/eat/drink),
  // everything else is worn (the server routes armor/light/held correctly)
  const USE_TYPES = ['potion', 'scroll', 'wand', 'staff', 'food', 'drink', 'pill', 'fountain'];
  // a weapon may arrive mislabeled (affixed/legendary gear), so damage_dice also
  // counts as "weapon"; anything with armor or a wear slot counts as wearable
  function isWeaponItem(item) {
    return String(item.item_type || item.type || '').toLowerCase() === 'weapon' || !!item.damage_dice;
  }
  function itemActionFor(item) {
    const t = String(item.item_type || item.type || '').toLowerCase();
    if (isWeaponItem(item)) return { verb: 'wield', label: 'double-click to wield' };
    if (USE_TYPES.includes(t) && !item.slot && item.armor == null) return { verb: 'use', label: 'double-click to use' };
    return { verb: 'wear', label: 'double-click to wear' };
  }
  // which equipment slot an inventory item targets (null if not equippable)
  function equipSlotKey(item) {
    if (!item) return null;
    if (isWeaponItem(item)) return 'wield';
    const t = String(item.item_type || item.type || '').toLowerCase();
    if (t === 'light') return 'light';
    if (item.slot) return item.slot;   // armor / worn / clothing / jewelry carry a wear_slot
    if (['potion', 'food', 'drink', 'scroll', 'pill', 'wand', 'staff', 'fountain', 'container', 'key', 'trash'].includes(t)) return null;
    return null;
  }
  // The MUD matches gear by substring of the FULL name, and wield/wear stop at
  // the first name match — so a last-word keyword ("winter") can hit the wrong
  // item and never reach the one you clicked. Use the whole name (minus a
  // leading article) for an unambiguous match; keep apostrophes since the
  // server compares against the real name.
  function equipKeyword(item) {
    // the cleaned name must remain a substring of the server's item.name, so
    // only strip a leading article + collapse whitespace — keep all other chars
    const full = String((item && item.name) || '').toLowerCase()
      .replace(/^(?:a|an|the|some)\s+/, '').replace(/\s+/g, ' ').trim();
    return full || MH.mobKeyword((item && item.name) || '');
  }
  const PAIRED_SLOTS = { finger: ['finger1', 'finger2'], neck: ['neck1', 'neck2'], wrist: ['wrist1', 'wrist2'] };
  // the equipped item currently occupying a given inventory item's slot
  function equippedCounterpart(eq, item) {
    if (!eq) return null;
    const slot = equipSlotKey(item);
    if (!slot) return null;
    return eq[slot] || eq[slot + '1'] || eq[slot + '2'] || null;
  }
  // the worn piece that must come off before the clicked item can go on. null =
  // the slot is free (empty, or a paired slot with a free side the server uses).
  function occupantToSwap(eq, item) {
    if (!eq) return null;
    const slot = equipSlotKey(item);
    if (!slot) return null;
    const paired = PAIRED_SLOTS[slot];
    if (paired) return paired.every(s => eq[s]) ? eq[paired[0]] : null;   // only if both full
    return eq[slot] || null;
  }
  // Click-to-equip with a real swap. Equipping has no class/level gate in this
  // MUD — it only fails on an occupied slot, the wrong keyword, or (for weapons
  // on a dual-wielder) the off-hand path. So: free the target slot first if it's
  // full, then wield/wear by the unique full name. Debounced so a double-click
  // doesn't fire twice. Consumables are simply used.
  let _equipLock = { key: '', ts: 0 };
  function swapEquip(item, action) {
    hideItemTip();
    const key = String((item && item.name) || '');
    const now = Date.now();
    if (_equipLock.key === key && now - _equipLock.ts < 600) return;   // de-dupe double-click
    _equipLock = { key, ts: now };
    const kw = equipKeyword(item);
    if (action.verb === 'use') {
      MH.sendCommand(`use ${kw}`);
      setTimeout(() => { MH.refreshState().then(renderInventory); }, 650);
      return;
    }
    // free an occupied slot first (also avoids the dual-wield off-hand path)
    const occ = occupantToSwap(MH.state.player && MH.state.player.equipment, item);
    if (occ) MH.sendCommand(`remove ${equipKeyword(occ)}`);
    const p = captureOutput(950);
    MH.sendCommand(`${action.verb} ${kw}`);
    p.then(lines => {
      const joined = lines.join('  ');
      if (!/you (?:wear|wield|hold|grip|light)\b/i.test(joined)) {
        const bad = lines.find(l => /you can'?t|cannot|don'?t have|must be|off-hand|already|no exit/i.test(l));
        if (bad) flash(bad.replace(/\x1b\[[0-9;]*m/g, '').slice(0, 100));
      }
    }).catch(() => {});
    setTimeout(() => { MH.refreshState().then(renderInventory); }, 750);
  }
  // remove a worn item by its unique full name (click or double-click a socket)
  function removeWorn(item) {
    if (!item) return;
    const key = 'rm:' + String(item.name || '');
    const now = Date.now();
    if (_equipLock.key === key && now - _equipLock.ts < 600) return;
    _equipLock = { key, ts: now };
    hideItemTip();
    MH.sendCommand(`remove ${equipKeyword(item)}`);
    setTimeout(() => { MH.refreshState().then(renderInventory); }, 600);
  }
  // stat-by-stat delta vs the currently equipped piece. Always renders for an
  // equippable item — comparing against the worn piece, or against an empty
  // slot (so weapons/armor always show what equipping them would change).
  function comparisonHTML(item, equipped, slot) {
    if (!slot) return '';
    const a = itemStatTotals(item), b = itemStatTotals(equipped);
    if (equipped && equipped.name === item.name) return '';
    const keys = [...new Set([...Object.keys(a), ...Object.keys(b)])];
    if (!keys.length) return '';
    let rows = '';
    keys.forEach(k => {
      const av = a[k] || 0, bv = b[k] || 0, d = Math.round((av - bv) * 10) / 10;
      const cls = d > 0 ? 'up' : d < 0 ? 'down' : 'same';
      const arrow = d > 0 ? '▲' : d < 0 ? '▼' : '=';
      rows += `<div class="it-cmp ${cls}"><span class="k">${k}</span><span class="v">${av}</span><span class="d">${arrow}${d !== 0 ? (d > 0 ? ' +' + d : ' ' + d) : ''}</span></div>`;
    });
    const head = equipped ? `vs equipped · ${equipped.name}` : `vs ${slot} slot · empty`;
    return `<div class="it-cmp-box"><div class="it-cmp-h">${head}</div>${rows}</div>`;
  }
  function itemTipHTML(item, action, compareTo, slot) {
    if (!item) return '';
    const rar = item.rarity || 'common';
    const type = item.item_type || item.type || 'item';
    const stat = (k, v) => `<div class="it-stat"><span class="k">${k}</span><span class="v">${v}</span></div>`;
    let h = `<div class="it-name ${rar}">${item.name}</div>`;
    const sub = [type];
    if (item.slot) sub.push(item.slot);
    if (item.level) sub.push('lvl ' + item.level);
    if (rar && rar !== 'common') sub.push(rar);
    h += `<div class="it-sub">${sub.join(' · ')}</div>`;
    if (item.damage_dice) h += stat('Damage', item.damage_dice + (item.weapon_type ? ` (${item.weapon_type})` : ''));
    if (item.armor) h += stat('Armor', '+' + item.armor);
    if (item.light_hours) h += stat('Light', item.light_hours + ' hrs');
    if (item.food_value) h += stat('Nourishment', item.food_value);
    if (item.drinks) h += stat('Drinks', item.drinks);
    (item.affects || []).forEach(a => {
      const t = a.type != null ? a.type : (a.location != null ? a.location : (a.applies_to != null ? a.applies_to : a.stat));
      const v = a.value != null ? a.value : a.modifier;
      if (t != null && t !== '' && v != null) h += `<div class="it-stat it-aff"><span class="k">${prettyStat(t)}</span><span class="v">${v > 0 ? '+' : ''}${v}</span></div>`;
    });
    (item.procs || []).forEach(pr => { if (pr) h += `<div class="it-proc">⚡ ${pr}</div>`; });
    h += comparisonHTML(item, compareTo, slot !== undefined ? slot : equipSlotKey(item));
    const foot = [];
    if (item.weight != null) foot.push(`⚖ ${item.weight}`);
    if (item.cost) foot.push(`🪙 ${item.cost}`);
    if (foot.length) h += `<div class="it-foot"><span>${foot[0] || ''}</span><span>${foot[1] || ''}</span></div>`;
    if (action) h += `<div class="it-hint">${action}</div>`;
    return h;
  }
  // short always-visible stat badge for a gear cell (weapon damage, armor, or
  // the item's headline enchantment) so stats are readable without hovering
  function itemStatBadge(item) {
    if (!item) return '';
    const t = item.item_type || item.type;
    if (t === 'weapon' && item.damage_dice) return `⚔ ${item.damage_dice}`;
    if (t === 'armor' && item.armor) return `🛡 +${item.armor}`;
    const a = (item.affects || [])[0];
    if (a) {
      const v = a.value != null ? a.value : a.modifier;
      const tt = a.type != null ? a.type : (a.location != null ? a.location : a.stat);
      if (tt != null && v != null) return `<span class="aff">${prettyStat(tt).slice(0, 3)} ${v > 0 ? '+' : ''}${v}</span>`;
    }
    return '';
  }
  let _itemTipEl = null;
  function showItemTip(item, ev, action, compareTo, slot) {
    if (!item) return;
    const tip = _itemTipEl || (_itemTipEl = document.getElementById('item-tip'));
    if (!tip) return;
    tip.innerHTML = itemTipHTML(item, action, compareTo, slot);
    tip.classList.add('show');
    moveItemTip(ev);
  }
  function moveItemTip(ev) {
    const tip = _itemTipEl;
    if (!tip || !tip.classList.contains('show')) return;
    const r = tip.getBoundingClientRect();
    let x = ev.clientX + 16, y = ev.clientY + 16;
    if (x + r.width > window.innerWidth - 8) x = ev.clientX - r.width - 14;
    if (y + r.height > window.innerHeight - 8) y = window.innerHeight - r.height - 8;
    tip.style.left = Math.max(8, x) + 'px';
    tip.style.top = Math.max(8, y) + 'px';
  }
  function hideItemTip() { if (_itemTipEl) _itemTipEl.classList.remove('show'); }

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

    // loot toggles + search/sort controls
    html += `<div class="inv-bar">`
      + `<span class="inv-toggle ${p.autoloot ? 'on' : ''}" data-toggle="autoloot" title="auto-loot corpses">🎒 loot</span>`
      + `<span class="inv-toggle ${p.autogold ? 'on' : ''}" data-toggle="autogold" title="auto-pick-up gold">🪙 gold</span>`
      + `<input id="inv-search" placeholder="search…" value="${invFilter.replace(/"/g, '')}">`
      + `<select id="inv-sort">`
      + ['slot:default', 'name:A–Z', 'type:type', 'rarity:rarity'].map(o => { const [v, l] = o.split(':'); return `<option value="${v}" ${invSort === v ? 'selected' : ''}>${l}</option>`; }).join('')
      + `</select></div>`;
    html += '<div class="inv-grid">';
    const RANK = { legendary: 5, epic: 4, rare: 3, uncommon: 2, common: 1 };
    let inv = (p.inventory || []).map((item, i) => ({ item, i }));
    if (invFilter) { const f = invFilter.toLowerCase(); inv = inv.filter(e => (e.item.name || '').toLowerCase().includes(f) || (e.item.item_type || e.item.type || '').toLowerCase().includes(f)); }
    if (invSort === 'name') inv.sort((a, b) => (a.item.name || '').localeCompare(b.item.name || ''));
    else if (invSort === 'type') inv.sort((a, b) => (a.item.item_type || a.item.type || '').localeCompare(b.item.item_type || b.item.type || ''));
    else if (invSort === 'rarity') inv.sort((a, b) => (RANK[b.item.rarity] || 0) - (RANK[a.item.rarity] || 0));
    if (!inv.length) html += `<div class="slot">${invFilter ? 'no matches' : 'empty-handed'}</div>`;
    inv.forEach(({ item, i }) => {
      const enchanted = (item.affects && item.affects.length) ? `<span class="inv-forge" data-kw="${MH.mobKeyword(item.name)}" title="reforge enchantments (gold)">⚒</span>` : '';
      const badge = itemStatBadge(item);
      html += `<div class="inv-cell" data-i="${i}" data-cmd="wear ${MH.mobKeyword(item.name)}" title="${item.name} (${item.item_type || 'item'})">`
        + `<canvas width="34" height="34"></canvas><span class="inv-nm">${(item.short || item.name).slice(0, 26)}</span>`
        + (badge ? `<span class="inv-stat">${badge}</span>` : '') + `${enchanted}</div>`;
    });
    html += '</div>';
    els.invBody.innerHTML = html;
    const allInv = p.inventory || [];
    els.invBody.querySelectorAll('.inv-toggle').forEach(t => t.addEventListener('click', () => {
      MH.sendCommand(t.dataset.toggle, false);
      setTimeout(() => { MH.refreshState().then(renderInventory); }, 500);
    }));
    const srch = document.getElementById('inv-search');
    if (srch) { srch.addEventListener('input', e => { invFilter = e.target.value; renderInventory(); setTimeout(() => { const s = document.getElementById('inv-search'); if (s) { s.focus(); s.setSelectionRange(s.value.length, s.value.length); } }, 0); });
      srch.addEventListener('keydown', e => e.stopPropagation()); }
    const srt = document.getElementById('inv-sort');
    if (srt) srt.addEventListener('change', e => { invSort = e.target.value; renderInventory(); });
    els.invBody.querySelectorAll('.inv-forge').forEach(fb => fb.addEventListener('click', e => {
      e.stopPropagation();
      MH.sendCommand(`reforge ${fb.dataset.kw}`, false);
      flash('⚒ reforging…');
      setTimeout(() => { MH.refreshState().then(renderInventory); }, 700);
    }));

    const model = els.invBody.querySelector('#pd-model');
    if (model) drawCharModel(model, p);
    els.invBody.querySelectorAll('.pd-socket').forEach(el => {
      const item = eq[el.dataset.slot];
      if (item && MH.itemIcons) MH.itemIcons.intoCanvas(el.querySelector('canvas'), item);
      if (item) {
        el.removeAttribute('title');   // replace the bare native title with the rich tooltip
        el.addEventListener('mouseenter', ev => showItemTip(item, ev, 'click to remove', null, null));
        el.addEventListener('mousemove', moveItemTip);
        el.addEventListener('mouseleave', hideItemTip);
        // a worn item comes off on click OR double-click
        el.addEventListener('click', () => removeWorn(item));
        el.addEventListener('dblclick', () => removeWorn(item));
      }
    });
    els.invBody.querySelectorAll('.inv-cell').forEach(el => {
      const item = allInv[Number(el.dataset.i)];
      if (!item) return;
      if (item && MH.itemIcons) MH.itemIcons.intoCanvas(el.querySelector('canvas'), item);
      el.removeAttribute('title');
      const action = itemActionFor(item);
      const slot = equipSlotKey(item);
      const cmp = equippedCounterpart(eq, item);
      el.addEventListener('mouseenter', ev => showItemTip(item, ev, action.label, cmp, slot));
      el.addEventListener('mousemove', moveItemTip);
      el.addEventListener('mouseleave', hideItemTip);
      // equip on click OR double-click (debounced so a double-click fires once)
      el.addEventListener('click', () => swapEquip(item, action));
      el.addEventListener('dblclick', () => swapEquip(item, action));
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
      if (q) q.addEventListener('click', e => { e.stopPropagation(); showAbilityHelp(el.dataset.help); });
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

  // a proper, structured character sheet built from the live player block —
  // no more raw MUD-text dump in the journal modal
  function openScore() {
    renderScore();
    openModal('modal-score');
  }
  function renderScore() {
    const p = MH.state.player || {};
    const body = $('score-body');
    if (!body) return;
    const cap = s => String(s || '').replace(/\b\w/g, c => c.toUpperCase());
    const bar = (cls, v, max, label) => {
      const pct = max > 0 ? Math.max(0, Math.min(100, (v / max) * 100)) : 0;
      return `<div class="sc-bar ${cls}"><i style="width:${pct}%"></i><b>${label}</b></div>`;
    };
    const stat = (k, v) => `<div class="sc-stat"><div class="v">${v != null ? v : '—'}</div><div class="k">${k}</div></div>`;
    const row = (k, v) => `<div class="sc-row"><span class="rk">${k}</span><span class="rv">${v}</span></div>`;
    const xpHave = (p.exp || 0) - (p.exp_floor || 0);
    const xpNeed = (p.exp_to_level || 0) - (p.exp_floor || 0);
    const xpOk = xpNeed > 0 && xpHave >= 0 && xpNeed < 1e12;
    const res = p.resource;
    let html = `<div class="sc-hd"><div class="sc-name">${p.name || 'Adventurer'}${p.title ? `<span class="sc-sub"> ${p.title}</span>` : ''}</div>`
      + `<div class="sc-sub">Level ${p.level || 1} · ${cap(p.race) || 'Adventurer'} ${cap(p.char_class)}</div></div>`;
    html += `<div class="sc-vitals">`
      + bar('hp', p.hp, p.max_hp, `Health ${p.hp || 0} / ${p.max_hp || 0}`)
      + bar('mana', p.mana, p.max_mana, `Mana ${p.mana || 0} / ${p.max_mana || 0}`)
      + bar('move', p.move, p.max_move, `Stamina ${p.move || 0} / ${p.max_move || 0}`)
      + bar('xp', xpOk ? xpHave : 1, xpOk ? xpNeed : 1, xpOk ? `XP ${xpHave.toLocaleString()} / ${xpNeed.toLocaleString()} to next level` : 'Experience · max level')
      + `</div>`;
    html += `<div class="sc-grid">`
      + stat('STR', p.str) + stat('INT', p.int) + stat('WIS', p.wis)
      + stat('DEX', p.dex) + stat('CON', p.con) + stat('CHA', p.cha) + `</div>`;
    html += `<div class="sc-sec">Combat</div><div class="sc-rows">`
      + row('Hitroll', `+${p.hitroll || 0}`) + row('Damroll', `+${p.damroll || 0}`)
      + row('Armor Class', p.armor_class != null ? p.armor_class : '—')
      + row('Stance', cap(p.position) || 'Standing')
      + (res && res.name ? row(res.name, `${res.value || 0}${res.max ? ' / ' + res.max : ''}`) : '')
      + `</div>`;
    html += `<div class="sc-sec">Wealth</div><div class="sc-rows">`
      + row('Gold', `${p.gold || 0}`)
      + `</div>`;
    body.innerHTML = html;
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
  // Show the help file for a single skill/spell/ability in the floating card,
  // cleaned of MUD frames — used by the training window and the spellbook so a
  // player can always learn what something does before spending on it.
  async function showAbilityHelp(topic) {
    const pretty = String(topic || '').replace(/_/g, ' ');
    if (MH.immersion) MH.immersion.showDetailCard(pretty, 'consulting the lore…', 'detail');
    const pr = captureOutput(2400);
    MH.sendCommand(`help ${pretty}`, false);
    const lines = await pr;
    let text = MH.cleanInfoText ? MH.cleanInfoText(lines.join('\n'), `help ${pretty}`) : lines.join('\n');
    if (!text.trim()) text = `No help entry for '${pretty}'. Try practicing it to learn by doing.`;
    if (MH.immersion) MH.immersion.showDetailCard(pretty, text, 'detail');
  }
  MH.showAbilityHelp = showAbilityHelp;

  // Controls & keybinds reference — the quick "how do I play this" card every
  // game should have. Built once, toggled open/closed.
  const CONTROLS_GUIDE = [
    ['Move & Explore', [
      ['W A S D', 'Walk around the room (or arrow keys)'],
      ['Shift+W/A/S/D', 'Travel through a room exit (N/S/E/W)'],
      ['Shift+Q / Shift+E', 'Go up / down'],
      ['Click ground', 'Walk there · click an exit on the compass to travel'],
      ['M', 'World map'],
    ]],
    ['Fight', [
      ['F or Space', 'Attack — engage · while fighting, press in the GOLD window for a PERFECT strike'],
      ['1 – 9, 0', 'Use the action-bar slot (skills & spells)'],
      ['Q / E / X', 'React to an enemy wind-up: Brace / Sidestep / Interrupt'],
      ['Move away', 'Walk OUT of a red danger zone to evade area attacks'],
      ['Bash / Kick', 'Break a 🛡 guarded enemy; fill their poise pips to STAGGER them'],
      ['Stance', 'Aggressive / Normal / Defensive — beside your vitals'],
    ]],
    ['Panels', [
      ['I', 'Inventory & equipment'],
      ['K / N', 'Abilities & spells / Talents'],
      ['J', 'Quests & journal'],
      ['C', 'Companions & mounts'],
      ['Y / B / V', 'Almanac / Services / Travel'],
      ['Z', 'Rest & recovery'],
      ['T', 'Chat'],
    ]],
    ['Environment', [
      ['G / B / V / L / P', 'By a door: Open · Bash · Barricade · Lock · Seal (chips appear)'],
      ['U', 'Disarm a detected trap (⚠ marker — or click it)'],
      ['O', 'Thief/Ranger: lay caltrops / a snare'],
      ['Search', 'Type search or detect traps to reveal hidden traps'],
    ]],
    ['Interact & Tips', [
      ['Right-click', 'Context menu (foe, player, yourself, objects)'],
      ['Enter', 'Type any command — its reply shows in a card'],
      ['Esc', 'Close panels / cancel'],
      ['H / ?', 'Game help / this controls card'],
      ['⚙', 'Settings: graphics, text size, sound, contrast'],
      ['`', 'Raw message log (drawer)'],
    ]],
  ];
  function openControls() {
    let ov = document.getElementById('controls-overlay');
    if (!ov) {
      ov = document.createElement('div');
      ov.id = 'controls-overlay';
      document.body.appendChild(ov);
    }
    const cols = CONTROLS_GUIDE.map(([sec, rows]) =>
      `<div class="co-sec">${sec}</div>` + rows.map(([k, d]) => {
        const keys = k.split(' ').map(part => /^[A-Za-z0-9`?+\/–-]+$/.test(part) && part.length <= 9 ? `<b>${part}</b>` : part).join(' ');
        return `<div class="co-row"><span class="co-key">${keys}</span><span class="co-desc">${d}</span></div>`;
      }).join('')).join('');
    ov.innerHTML = `<div class="co-card"><div class="co-h">⌨ CONTROLS</div>`
      + `<div class="co-sub">Everything is also clickable — and you can type any command with Enter.</div>`
      + `<div class="co-cols">${cols}</div><button class="co-close">Got it</button></div>`;
    ov.classList.add('show');
    const close = () => ov.classList.remove('show');
    ov.querySelector('.co-close').addEventListener('click', close);
    ov.addEventListener('click', e => { if (e.target === ov) close(); });
    if (MH.sfx) MH.sfx.ui();
  }
  MH.openControls = openControls;

  async function openHelp(topic) {
    openModal('modal-journal');
    const head = document.querySelector('#modal-journal .modal-head span');
    if (head) head.textContent = 'HELP';
    els.journalBody.innerHTML = '<div class="help-panel"><input id="help-search" class="help-search" type="text" '
      + 'placeholder="search help… (e.g. fireball, stance, path)"><div id="help-text" class="help-text">…</div></div>';
    const input = document.getElementById('help-search');
    const out = document.getElementById('help-text');
    const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const fmt = txt => {
      const lines = txt.split('\n').filter(l => !/^[=_]{5,}$/.test(l.trim()));
      let h = '', titled = false;
      for (const line of lines) {
        const t = line.trim();
        if (!t) { h += '<div class="hl-sp"></div>'; continue; }
        if (!titled) { h += `<div class="hl-title">${esc(t)}</div>`; titled = true; continue; }
        const lab = t.match(/^([A-Z][A-Z &/]{2,}):\s*(.*)$/);
        if (lab) h += `<div class="hl-row"><span class="hl-k">${esc(lab[1])}</span> <span class="hl-v">${esc(lab[2])}</span></div>`;
        else h += `<div class="hl-line">${esc(t)}</div>`;
      }
      return h;
    };
    const show = async t => {
      out.innerHTML = '<div class="hl-line">…</div>';
      const pr = captureOutput(2400);
      MH.sendCommand(t ? `help ${t}` : 'help', false);
      const lines = await pr;
      const txt = lines.join('\n').trim();
      out.innerHTML = txt ? fmt(txt) : '<div class="hl-line">(no help text came back)</div>';
      out.scrollTop = 0;
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
    const jh = document.querySelector('#modal-journal .modal-head span');
    if (jh) jh.textContent = 'QUEST JOURNAL';
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
          + `<span class="sr-help" data-help="${a.id}" title="what does ${pretty} do?">ⓘ</span>`
          + `<span class="sr-price">${mastered ? 'MASTERED' : a.prof + '%'}</span></div>`;
      }
      return h + '</div>';
    };
    html += section('SKILLS', d.skills, 'star');
    html += section('SPELLS', d.spells, 'sparkle');
    els.shopBody.innerHTML = html;
    els.shopBody.querySelectorAll('.sr-help').forEach(q => q.addEventListener('click', e => {
      e.stopPropagation();
      showAbilityHelp(q.dataset.help);
    }));
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
  // distinct art per mount type (the stable used one horse icon for everything)
  const MOUNT_ICON = {
    horse: '🐴', pony: '🐴', warhorse: '🐎', nightmare: '🔥🐎',
    griffin: '🦅', clockwork_steed: '⚙️', donkey: '🫏',
  };
  function mountIcon(o) {
    const byKey = MOUNT_ICON[String((o && o.key) || '').toLowerCase()];
    if (byKey) return byKey;
    return o && o.can_fly ? '🦅' : '🐴';
  }
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
        const loy = (o.loyalty != null) ? ` · loyalty ${o.loyalty}%` : '';
        const feats = [o.can_fly ? 'flight' : '', o.combat_ok ? 'combat-ready' : '', `+${Math.round(o.speed_bonus * 100)}% speed`].filter(Boolean).join(' · ') + loy;
        html += `<div class="st-card ${o.active ? 'active' : ''}"><div class="st-ic">${mountIcon(o)}</div><div class="st-m">`
          + `<div class="st-n">${o.name}${o.active ? '<span class="tag">riding</span>' : ''}</div><div class="st-d">${feats}</div></div>`
          + (o.active ? `<button class="st-btn" id="st-dismount">DISMOUNT</button>`
                      : `<button class="st-btn go" data-mount="${o.key}">RIDE</button>`) + `</div>`;
      }
      html += `<div class="st-hd">🏪 STABLE${m.at_stable ? '' : ' (find a stable to buy)'}</div>`;
      for (const pu of m.purchasable) {
        const can = m.at_stable && pu.afford;
        html += `<div class="st-card"><div class="st-ic">${mountIcon(pu)}</div><div class="st-m">`
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

  // ---- fast travel / waypoints ----
  async function openTravel() {
    openModal('modal-travel');
    els.travelBody.innerHTML = '<div class="slot">consulting the maps…</div>';
    let d;
    try { d = await (await fetch(`/travel?player=${encodeURIComponent(MH.state.playerName)}`)).json(); }
    catch (_) { els.travelBody.innerHTML = '<div class="slot">travel unavailable</div>'; return; }
    let html = `<div class="tv-hd">🗺 DISCOVERED WAYPOINTS · ${d.discovered}/${d.total}</div>`;
    html += `<div class="tv-sub">🪙 ${d.gold.toLocaleString()} gold`
      + (d.cooldown > 0 ? ` · ⏳ ready in ${d.cooldown}s` : '') + `</div>`;
    if (!d.waypoints.length) html += `<div class="alm-note" style="text-align:left">No waypoints discovered yet — explore zone entrances to unlock fast travel.</div>`;
    for (const w of d.waypoints) {
      const poor = w.cost > d.gold;
      const cls = w.here ? 'here' : poor ? 'poor' : '';
      html += `<div class="tv-row ${cls}" data-key="${w.key}" data-ok="${!w.here && !poor && d.cooldown <= 0}">`
        + `<span class="tn">${w.name}</span>`
        + `<span class="tc">${w.here ? '◈ you are here' : w.cost + 'g'}</span></div>`;
    }
    els.travelBody.innerHTML = html;
    els.travelBody.querySelectorAll('.tv-row').forEach(row => {
      if (row.dataset.ok !== 'true') return;
      row.addEventListener('click', () => {
        MH.sendCommand(`travel ${row.dataset.key}`, false);
        flash('Traveling…'); closeModals();
      });
    });
  }

  // ---- recovery: rest/sleep regeneration panel ----
  const REST_POS = [
    { key: 'stand', pos: 'standing', ic: '🧍', label: 'Stand' },
    { key: 'sit', pos: 'sitting', ic: '🪑', label: 'Sit' },
    { key: 'rest', pos: 'resting', ic: '🍵', label: 'Rest' },
    { key: 'sleep', pos: 'sleeping', ic: '💤', label: 'Sleep' },
  ];
  let recoveryOpen = false, recoveryData = null, recoveryTimer = null;
  function toggleRecovery(on) {
    recoveryOpen = on != null ? on : !recoveryOpen;
    els.recoveryPanel.classList.toggle('show', recoveryOpen);
    clearInterval(recoveryTimer);
    if (recoveryOpen) { refreshRecovery(); recoveryTimer = setInterval(refreshRecovery, 4000); }
  }
  function refreshRecovery() {
    if (!MH.state.playerName) return;
    fetch(`/regen?player=${encodeURIComponent(MH.state.playerName)}`)
      .then(r => r.json()).then(d => { recoveryData = d; setRestChipPos(d.position); renderRecovery(); }).catch(() => {});
  }
  function setRestChipPos(pos) {
    const resting = pos === 'resting' || pos === 'sleeping' || pos === 'sitting';
    els.restChip.classList.toggle('show', resting);
    if (resting) {
      const ic = pos === 'sleeping' ? '💤' : pos === 'resting' ? '🍵' : '🪑';
      els.restChip.textContent = `${ic} ${pos} — recovering (Z)`;
    }
  }
  function renderRecovery() {
    const d = recoveryData; if (!d || !recoveryOpen) return;
    const cur = d.position || 'standing';
    const r = d.rates[cur] || d.rates.standing;
    const best = d.rates.sleeping;
    const pct = (v, max) => Math.max(4, Math.min(100, (v / Math.max(1, max)) * 100));
    let html = `<div class="rp-hd">RECOVERY · ${cur.toUpperCase()}</div><div class="rp-pos">`;
    for (const p of REST_POS) {
      const on = p.pos === cur ? ' on' : '';
      const combat = d.in_combat && p.key !== 'stand' ? ' combat' : '';
      html += `<div class="rp-btn${on}${combat}" data-cmd="${p.key}"><span class="ic">${p.ic}</span>${p.label}</div>`;
    }
    html += `</div><div class="rp-rates">`;
    const rows = [['hp', 'HP', '#7fe09a'], ['mana', 'MP', '#5a8ae8'], ['move', 'MV', '#e8c168']];
    const cls = { hp: 'hp', mana: 'mp', move: 'mv' };
    for (const [k, lbl] of rows) {
      html += `<div class="rp-rate"><span class="rl">${lbl}</span>`
        + `<span class="rt ${cls[k]}"><i style="width:${pct(r[k], best[k])}%"></i></span>`
        + `<span class="rv">+${r[k]}/min ${cur !== 'sleeping' ? `<small>(💤 +${best[k]})</small>` : ''}</span></div>`;
    }
    html += `</div>`;
    if (d.modifiers && d.modifiers.length) {
      html += `<div class="rp-mods">` + d.modifiers.map(m => `<span class="rp-mod">${m.icon} ${m.label}</span>`).join('') + `</div>`;
    }
    if (d.at_inn && d.rent_cost != null) {
      const poor = d.gold < d.rent_cost;
      html += `<button class="rp-rent ${poor ? 'poor' : ''}" id="rp-rent" ${poor ? 'disabled' : ''}>🛏 Rent &amp; log out · ${d.rent_cost}g</button>`;
    }
    els.recoveryPanel.innerHTML = html;
    els.recoveryPanel.querySelectorAll('.rp-btn').forEach(b => {
      if (b.classList.contains('combat')) return;
      b.addEventListener('click', () => { MH.sendCommand(b.dataset.cmd, false); setTimeout(() => { refreshRecovery(); MH.refreshState && MH.refreshState(); }, 500); });
    });
    const rent = document.getElementById('rp-rent');
    if (rent && !rent.disabled) rent.addEventListener('click', () => { MH.sendCommand('rent', false); flash('Renting…'); });
  }
  // persistent resting chip + regen float on bars
  function updateRestChip(player) {
    if (!player) return;
    const pos = player.position || 'standing';
    const resting = pos === 'resting' || pos === 'sleeping' || pos === 'sitting';
    setRestChipPos(pos);
    // float +N on the HP bar when vitals climb while recovering
    if (resting && updateRestChip._hp != null && player.hp > updateRestChip._hp) {
      floatRegen(player.hp - updateRestChip._hp);
    }
    updateRestChip._hp = player.hp;
  }
  function floatRegen(amt) {
    const host = els.hud; if (!host) return;
    const f = document.createElement('div');
    f.textContent = `+${Math.round(amt)}`;
    f.style.cssText = 'position:absolute;left:74px;top:6px;color:#7fe09a;font-size:13px;font-weight:700;pointer-events:none;text-shadow:0 0 3px #000;z-index:30;animation:pf-pop 1s ease-out forwards';
    host.appendChild(f);
    setTimeout(() => f.remove(), 1000);
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
    const s = cell - 2, rad = Math.min(3, s / 3);
    const rcell = (x, y, w, h, rr) => {
      if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(x, y, w, h, rr); ctx.fill(); }
      else ctx.fillRect(x, y, w, h);
    };
    // corridor links between adjacent explored rooms, drawn UNDER the cells so
    // the map reads as a connected network rather than scattered dots
    const onLevel = {};
    for (const r of (payload.rooms || [])) if ((r.z || 0) === z) onLevel[r.x + ',' + r.y] = 1;
    ctx.strokeStyle = 'rgba(120,165,200,0.3)';
    ctx.lineWidth = Math.max(1, cell * 0.12);
    ctx.lineCap = 'round';
    for (const r of (payload.rooms || [])) {
      if ((r.z || 0) !== z) continue;
      const cxp = W / 2 + (r.x - p.x) * cell, cyp = H / 2 + (r.y - p.y) * cell;
      for (const [dx, dy] of [[1, 0], [0, 1]]) {   // east + south avoids double-drawing
        if (onLevel[(r.x + dx) + ',' + (r.y + dy)]) {
          ctx.beginPath(); ctx.moveTo(cxp, cyp); ctx.lineTo(cxp + dx * cell, cyp + dy * cell); ctx.stroke();
        }
      }
    }
    for (const r of (payload.rooms || [])) {
      if ((r.z || 0) !== z) continue;
      const x = W / 2 + (r.x - p.x) * cell - s / 2;
      const y = H / 2 + (r.y - p.y) * cell - s / 2;
      if (x < -cell || x > W || y < -cell || y > H) continue;
      const here = r.vnum === p.vnum;
      if (here) {
        // current room: cyan with a soft glow ring
        ctx.save();
        ctx.shadowColor = '#39c5e8'; ctx.shadowBlur = 8;
        ctx.fillStyle = '#39c5e8'; ctx.globalAlpha = 1;
        rcell(x, y, s, s, rad);
        ctx.restore();
      } else {
        ctx.fillStyle = r.vnum === walkTargetVnum ? '#e8c168' : (zoneColor[r.zone] || '#3a5566');
        ctx.globalAlpha = 0.5;
        rcell(x, y, s, s, rad);
      }
      ctx.globalAlpha = 1;
      // up/down markers
      if ((r.exits || []).includes('up') || (r.exits || []).includes('down')) {
        ctx.fillStyle = '#cfe6f0';
        ctx.fillRect(x + s / 2 - 1, y + s / 2 - 1, 1, 1);
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
  let wmZoom = 1;                       // big-map zoom multiplier (zone view)
  const WM_ZOOM_MIN = 1, WM_ZOOM_MAX = 5;
  function wmSetZoom(z) {
    const nz = Math.max(WM_ZOOM_MIN, Math.min(WM_ZOOM_MAX, Math.round(z * 100) / 100));
    if (nz === wmZoom) return;
    wmZoom = nz;
    const lbl = document.getElementById('wm-zoom-lvl');
    if (lbl) lbl.textContent = Math.round(wmZoom * 100) + '%';
    wmRender();
  }
  // zooming from the world overview drills into the zone you are standing in
  function drillHome() {
    const payload = MH.state.lastPayload;
    if (!payload || !payload.player) return;
    const atlas = MH.state.atlas;
    let here = (payload.rooms || []).find(r => r.vnum === payload.player.vnum);
    if (!here && atlas && atlas.byVnum) here = atlas.byVnum.get(payload.player.vnum);
    if (here && here.zone != null) { wmZoneId = here.zone; wmView = 'zone'; }
  }
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
      wmSetZoom(1);
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
        wmZoom = 1;
        const zlbl = document.getElementById('wm-zoom-lvl');
        if (zlbl) zlbl.textContent = '100%';
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
    const baseCell = Math.max(7, Math.min(26,
      Math.min((rect.width - PAD * 2) / (x1 - x0 + 1), (rect.height - PAD * 2) / (y1 - y0 + 1))));
    const cell = baseCell * wmZoom;
    const me0 = rooms.find(r => r.vnum === payload.player.vnum);
    let offX, offY;
    if (wmZoom > 1 && me0) {
      // when zoomed in, pan so the player's room stays centred
      offX = rect.width / 2 - ((me0.x - x0) * cell + cell / 2);
      offY = rect.height / 2 - ((me0.y - y0) * cell + cell / 2);
    } else {
      offX = (rect.width - (x1 - x0 + 1) * cell) / 2;
      offY = (rect.height - (y1 - y0 + 1) * cell) / 2;
    }
    const doClamp = wmZoom <= 1;   // only squeeze outliers to the edge at full extent
    const clampX = v => doClamp ? Math.max(14, Math.min(rect.width - 14, v)) : v;
    const clampY = v => doClamp ? Math.max(14, Math.min(rect.height - 14, v)) : v;
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
      // the world now renders inside the camera viewport; its right edge (in
      // page px) marks where the UI band begins
      const fx = gc.width / sc.scale.width;
      const worldRight = gc.left + (cam.x + cam.width) * fx;
      band = window.innerWidth - worldRight;
    } catch (_) { /* scene not up yet */ }
    const w = Math.round(Math.max(150, Math.min(300, band - 26)));
    els.minimap.width = mmLarge ? Math.max(w, 300) : w;
    els.minimap.height = mmLarge ? 420 : 150;   // compact sector map (Aether spec)
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
      const door = has && exits[dir].door;
      const closed = door && door.state !== 'open';
      const hidden = has && exits[dir].hidden;
      const danger = has && exits[dir].deathtrap;
      const cls = dir == null ? 'cmp spacer' : `cmp${has ? ' on' : ''}${zone ? ' zone' : ''}${door ? ' door' : ''}${closed ? ' closed' : ''}${hidden ? ' hidden' : ''}${danger ? ' deathtrap' : ''}`;
      const title = danger ? ` title="⚠ DANGER — certain death lies ${dir}"`
        : door ? ` title="${closed ? (door.locked ? 'locked' : 'closed') : 'open'} ${door.name}${hidden ? ' (hidden)' : ''} — click for door controls"`
        : hidden ? ` title="hidden passage ${dir}"` : (zone ? ` title="→ ${zone}"` : '');
      const mark = danger ? `<span class="cmp-door cmp-danger">☠</span>`
        : door ? `<span class="cmp-door">${door.locked && closed ? '🔒' : closed ? '🚪' : '◙'}</span>`
        : (hidden ? `<span class="cmp-door cmp-secret">❓</span>` : '');
      return `<div class="${cls}" ${has ? `data-dir="${dir}"` : ''}${title}>${label}${mark}</div>`;
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
    els.compass.querySelectorAll('.cmp.on').forEach(el => {
      const dir = el.dataset.dir;
      const door = exits[dir] && exits[dir].door;
      const danger = exits[dir] && exits[dir].deathtrap;
      el.addEventListener('click', e => {
        if (door) { doorDialogue(dir, door, e.clientX, e.clientY); return; }
        if (danger && !window.confirm(`⚠ DANGER: heading ${dir} leads to certain death. Go anyway?`)) return;
        MH.bus.emit('nav.goto', dir);
      });
    });
  }
  // a small open/close dialogue for a doorway, anchored on the compass cell
  function doorDialogue(dir, door, x, y) {
    if (!MH.popover) { MH.sendCommand(`${door.state === 'open' ? 'close' : 'open'} ${door.name} ${dir}`); return; }
    const nm = door.name || 'door';
    const closed = door.state !== 'open';
    const acts = [];
    if (closed) {
      if (door.locked) acts.push({ label: `🔓 Unlock ${nm}`, fn: () => MH.sendCommand(`unlock ${nm} ${dir}`) });
      acts.push({ label: `🚪 Open ${nm}`, fn: () => MH.sendCommand(`open ${nm} ${dir}`) });
    } else {
      acts.push({ label: `🚪 Close ${nm}`, fn: () => MH.sendCommand(`close ${nm} ${dir}`) });
    }
    acts.push({ label: `🧭 Go ${dir}`, fn: () => MH.bus.emit('nav.goto', dir) });
    MH.popover.show(x, y, `${nm} (${dir})`, acts);
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
        + `<span class="eusage">${ab.usage} uses${next ? ` · next at ${next}` : ' · fully evolved path'}</span>`
        + `<span class="eacts"><button class="ebtn use" data-use="${ab.ability}" title="use ${ab.ability} now">▶ Use</button>`
        + `<button class="ebtn bind" data-bind="${ab.ability}" title="add to action bar">⊕ Bar</button>`
        + `<button class="ebtn help" data-abhelp="${ab.ability}" title="what does ${ab.ability} do?">ⓘ</button></span></div>`
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
    // use an ability now (no typing) — closes the panel so you see it land
    els.talentsBody.querySelectorAll('[data-use]').forEach(btn => {
      btn.addEventListener('click', () => {
        const ab = btn.dataset.use;
        // target-needing abilities use the current target if there is one
        const tgt = currentTarget && currentTarget.name ? ' ' + MH.mobKeyword(currentTarget.name) : '';
        MH.sendCommand(`${ab}${tgt}`);
        closeModals();
      });
    });
    // bind an ability to the action bar
    els.talentsBody.querySelectorAll('[data-bind]').forEach(btn => {
      btn.addEventListener('click', () => { if (bindToHotbar(btn.dataset.bind)) flash(`${btn.dataset.bind} added to your action bar`); });
    });
    // show the help file for the ability
    els.talentsBody.querySelectorAll('[data-abhelp]').forEach(btn => {
      btn.addEventListener('click', e => { e.stopPropagation(); showAbilityHelp(btn.dataset.abhelp); });
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
    els.dialogueBody.innerHTML = '<div class="npc-speech slot">…</div>';
    const kw = MH.mobKeyword(name);
    const p1 = captureOutput(1300);
    MH.sendCommand(`talk ${kw}`, false);
    const talkLines = await p1;
    const NOISE = /quest accept|\*npc\*|notable figure encountered|^type '?journal'?|to view your discoveries/i;
    const saidClean = MH.cleanInfoText ? MH.cleanInfoText(talkLines.join('\n'), `talk ${kw}`) : talkLines.join('\n');
    const said = saidClean.split('\n').filter(l => l.trim() && !NOISE.test(l) && l.trim().toLowerCase() !== name.toLowerCase());
    let inner = `<div class="npc-head"><canvas class="npc-portrait" width="44" height="44"></canvas>`
      + `<div class="npc-id"><div class="npc-nm">${name}</div><div class="npc-role">${quest ? '✦ Quest Giver' : 'Townsfolk'}</div></div></div>`;
    if (said.length) inner += `<div class="npc-speech">${said.slice(0, 10).map(l => l.replace(/</g, '&lt;')).join('<br>')}</div>`;
    if (quest) {
      const p2 = captureOutput(1300);
      MH.sendCommand('quest', false);
      const qLines = await p2;
      const offers = [];
      talkLines.concat(qLines).forEach(l => {
        const m = l.match(/quest accept (\S+)/i);
        const id = m && m[1].replace(/\)$/, '');
        if (id && /^[a-z0-9_]+$/i.test(id) && !offers.includes(id)) offers.push(id);
      });
      const qClean = MH.cleanInfoText ? MH.cleanInfoText(qLines.join('\n'), 'quest') : qLines.join('\n');
      const qText = qClean.split('\n').filter(l => l.trim() && !NOISE.test(l)).slice(0, 16);
      if (qText.length) inner += `<div class="npc-quest">${qText.map(l => l.replace(/</g, '&lt;')).join('<br>')}</div>`;
      if (offers.length) {
        inner += '<div class="npc-actions">'
          + offers.map(id => `<span class="quest-btn" data-q="${id}">✦ Accept: ${id.replace(/_/g, ' ')}</span>`).join('')
          + '</div>';
      } else if (quest === '?') {
        inner += `<div class="npc-actions"><span class="quest-btn turnin" data-turnin="1">✔ Turn in quest</span></div>`;
      }
    }
    els.dialogueBody.innerHTML = `<div class="npc-dialogue">${inner}</div>`;
    // draw the NPC's pixel portrait into the header
    const cv = els.dialogueBody.querySelector('.npc-portrait');
    if (cv) { const sc = MH.game && MH.game.scene.getScenes(true).find(s => s.mobPortrait); if (sc) try { sc.mobPortrait(cv, name); } catch (_) {} }
    if (!said.length && !els.dialogueBody.querySelector('.npc-quest') && !els.dialogueBody.querySelector('.quest-btn')) {
      els.dialogueBody.querySelector('.npc-dialogue').insertAdjacentHTML('beforeend', '<div class="npc-speech slot">They have nothing to say.</div>');
    }
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
        legendBody: $('legend-body'), questTracker: $('quest-tracker'), travelBody: $('travel-body'),
        restChip: $('rest-chip'), recoveryPanel: $('recovery-panel'),
        welcomeOverlay: $('welcome-overlay'), welcomeBody: $('welcome-body'), welcomeGo: $('welcome-go'),
      });

      // panels (modals + combat log + chat) can be dragged by their headers
      setupDraggables();

      // login
      const savedName = lsGet(NAME_KEY), savedPw = lsGet(PW_KEY);
      if (savedName) els.loginName.value = savedName;
      if (savedPw) { try { els.loginPass.value = atob(savedPw); } catch (_) {} }
      const begin = create => {
        const name = els.loginName.value.trim(), pass = els.loginPass.value;
        if (!name || !pass) { els.loginStatus.textContent = 'Need both name and password.'; els.loginStatus.className = 'error'; return; }
        if (create && !/^[a-zA-Z]{3,12}$/.test(name)) {
          els.loginStatus.textContent = 'Name must be 3–12 letters (no spaces, numbers, or symbols).';
          els.loginStatus.className = 'error';
          return;
        }
        if (create) {
          creationMode = true;
          cwShow(true);
          cwWaiting('Summoning the loom of fate…');
        }
        MH.connect(name, pass, create);
      };
      // ---------------- character creation wizard ----------------
      const CW_CLASSES = [
        ['warrior', '⚔', 'Master of melee and defense — sturdy and relentless.', 'STR'],
        ['mage', '🔮', 'Commands devastating arcane spells from afar.', 'INT'],
        ['cleric', '✨', 'Divine healer who mends allies and smites the undead.', 'WIS'],
        ['thief', '🗡', 'Cunning rogue who strikes from the shadows.', 'DEX'],
        ['ranger', '🏹', 'Wilderness warrior blending blade and nature magic.', 'DEX'],
        ['paladin', '🛡', 'Holy warrior — martial skill fused with divine power.', 'STR'],
        ['necromancer', '💀', 'Dark mage who commands death and the undead.', 'INT'],
        ['bard', '🎵', 'Charismatic performer who inspires with magical songs.', 'CHA'],
        ['assassin', '🥷', 'Deadly killer who eliminates targets with precision.', 'DEX'],
      ];
      const CW_RACES = [
        ['human', '🧑', 'Versatile and balanced — at home anywhere.'],
        ['elf', '🧝', 'Graceful and magical, keen of mind and eye.'],
        ['dwarf', '🧔', 'Sturdy and tough, hewn from living stone.'],
        ['halfling', '🧒', 'Nimble and lucky — small, quick, hard to hit.'],
        ['half_orc', '👹', 'Fierce and mighty, a born brawler.'],
        ['gnome', '🧙', 'Clever and arcane, a tinkering mind.'],
        ['dark_elf', '🦇', 'Deadly shadow-kin, swift and merciless.'],
      ];
      let creationMode = false, cwPrime = '';
      const cw = id => document.getElementById(id);
      const cwShow = on => cw('create-wizard').classList.toggle('show', on);
      const cwSend = v => { const s = MH.state.mudSocket; if (s && s.readyState === WebSocket.OPEN) s.send(v); cw('cw-status').textContent = '✦ Forging…'; if (MH.sfx) MH.sfx.ui(); };
      const cap = s => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      function cwWaiting(msg) { cw('cw-steps').textContent = ''; cw('cw-sub').textContent = ''; cw('cw-body').innerHTML = `<div style="text-align:center;color:#9aa0b4;padding:30px 0">${msg}</div>`; }
      function cwGrid(items, races) {
        return `<div id="cw-grid"${races ? ' class="races"' : ''}>` + items.map(it => {
          const [id, ic, de, st] = it;
          return `<div class="cw-pick" data-v="${id}"><span class="cw-ic">${ic}</span><span class="cw-nm">${cap(id)}</span>`
            + `<div class="cw-de">${de}</div>${st ? `<div class="cw-st">Prime: ${st}</div>` : ''}</div>`;
        }).join('') + '</div>';
      }
      function cwBindPicks(onPick) {
        cw('cw-body').querySelectorAll('.cw-pick').forEach(el => el.addEventListener('click', () => onPick(el.dataset.v)));
      }
      function cwRace() {
        cw('cw-title').textContent = '⚔ CHOOSE YOUR LINEAGE'; cw('cw-steps').textContent = 'STEP 1 OF 3';
        cw('cw-sub').textContent = 'Your bloodline shapes your gifts and your fate.';
        cw('cw-body').innerHTML = cwGrid(CW_RACES, true);
        cwBindPicks(v => cwSend(v));
      }
      function cwClass() {
        cw('cw-title').textContent = '⚔ CHOOSE YOUR CALLING'; cw('cw-steps').textContent = 'STEP 2 OF 3';
        cw('cw-sub').textContent = 'Your class is how you fight, cast, and grow.';
        cw('cw-body').innerHTML = cwGrid(CW_CLASSES);
        cwBindPicks(v => { const c = CW_CLASSES.find(x => x[0] === v); cwPrime = c ? c[3] : ''; cwSend(v); });
      }
      function cwStats(text) {
        cw('cw-title').textContent = '⚔ ROLL YOUR FATE'; cw('cw-steps').textContent = 'STEP 3 OF 3';
        cw('cw-sub').textContent = 'The dice favor the bold — keep them, or tempt fate again.';
        const map = { Strength: 'STR', Intelligence: 'INT', Wisdom: 'WIS', Dexterity: 'DEX', Constitution: 'CON', Charisma: 'CHA' };
        const re = /(Strength|Intelligence|Wisdom|Dexterity|Constitution|Charisma):\s*(\d+)/g;
        let m, cells = '';
        while ((m = re.exec(text))) { const k = map[m[1]]; cells += `<div class="cw-stat ${k === cwPrime ? 'prime' : ''}"><div class="v">${m[2]}</div><div class="k">${k}</div></div>`; }
        cw('cw-body').innerHTML = `<div class="cw-stats">${cells}</div><div class="cw-btns"><button class="cw-btn go" id="cw-keep">⚑ Keep these</button><button class="cw-btn" id="cw-reroll">↻ Reroll</button></div>`;
        cw('cw-keep').addEventListener('click', () => cwSend('y'));
        cw('cw-reroll').addEventListener('click', () => cwSend('n'));
      }
      MH.bus.on('terminal.output', ({ text }) => {
        if (!creationMode || MH.state.isLoggedIn || !text) return;
        if (/choose your race|race name or number/i.test(text)) { cwRace(); cw('cw-status').textContent = ''; return; }
        if (/choose your class|class name or number/i.test(text)) { cwClass(); cw('cw-status').textContent = ''; return; }
        if (/accept these stats|to reroll/i.test(text) || /Strength:\s*\d+/.test(text)) { cwStats(text); cw('cw-status').textContent = ''; return; }
        // surface name-taken / invalid notices, with a way to start over
        const note = text.split('\n').map(l => l.trim()).filter(l => l && !/^[═=]+$/.test(l) && !/forging|opening the gate/i.test(l)).slice(-1)[0];
        if (note && /invalid|already|taken|try again|not a valid|must (?:be|contain)|in use/i.test(note)) {
          cw('cw-status').innerHTML = `${note.slice(0, 120)} <span id="cw-back">↻ start over</span>`;
          const back = document.getElementById('cw-back');
          if (back) back.addEventListener('click', () => location.reload());
        }
      });
      MH.bus.on('login.success', () => { creationMode = false; cwShow(false); });
      MH.bus.on('create.blocked', msg => {
        if (!creationMode) return;
        cw('cw-title').textContent = '⚔ FORGE YOUR HERO'; cw('cw-steps').textContent = ''; cw('cw-sub').textContent = '';
        cw('cw-body').innerHTML = `<div style="text-align:center;color:#e0a07a;padding:24px 12px;line-height:1.6">${msg}`
          + `<br><br><span id="cw-back">↻ start over</span></div>`;
        const back = document.getElementById('cw-back');
        if (back) back.addEventListener('click', () => location.reload());
      });
      els.loginBtn.addEventListener('click', () => begin(false));
      els.createBtn.addEventListener('click', () => begin(true));
      els.loginPass.addEventListener('keydown', e => { if (e.key === 'Enter') begin(false); });

      MH.bus.on('login.status', msg => { els.loginStatus.textContent = msg; els.loginStatus.className = ''; });
      MH.bus.on('login.error', msg => { els.loginStatus.textContent = msg; els.loginStatus.className = 'error'; });
      MH.bus.on('login.success', () => {
        els.loginOverlay.classList.add('hidden');
        lsSet(NAME_KEY, MH.state.playerName);
        lsSet(PW_KEY, btoa(MH.state.playerPassword));
        // bridge the gap before the first room paints with a themed loader
        const bl = document.getElementById('boot-loader');
        if (bl && !bl.dataset.done) {
          bl.classList.add('show');
          const finish = () => {
            if (bl.dataset.done) return;
            bl.dataset.done = '1';
            bl.classList.add('fade');
            setTimeout(() => bl.classList.remove('show', 'fade'), 750);
          };
          MH.bus.on('room.entered', () => setTimeout(finish, 350));
          setTimeout(finish, 4500);   // fallback so it never sticks
        }
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
      // position commands don't trigger a map push (you don't move), so pull
      // fresh state to update the recovery pose + chip + panel
      MH.bus.on('terminal.echo', cmd => {
        if (/^(sleep|rest|sit|stand|wake)\b/i.test(String(cmd).trim())) {
          setTimeout(() => { if (MH.refreshState) MH.refreshState(); if (recoveryOpen) refreshRecovery(); }, 350);
        }
      });
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
            if (a.daily && !a.daily.claimed_today) toast('🌟 Daily reward ready', 'Click to claim · streak ' + a.daily.streak, 'daily', () => openAlmanac('daily'));
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
          // opening Channels/Party issues the matching command server-side so
          // the social beginner quests count from the UI too
          if (activeTab === 'channel') { try { MH.sendCommand('channel list', false); } catch (_) {} }
          else if (activeTab === 'party') { try { MH.sendCommand('group', false); } catch (_) {} }
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
      // big-map zoom: +/- buttons and mouse wheel over the body
      const wmZoomIn = $('wm-zoom-in'), wmZoomOut = $('wm-zoom-out');
      if (wmZoomIn) wmZoomIn.addEventListener('click', () => { if (wmView === 'world') drillHome(); wmSetZoom(wmZoom + 0.5); });
      if (wmZoomOut) wmZoomOut.addEventListener('click', () => wmSetZoom(wmZoom - 0.5));
      $('wm-body').addEventListener('wheel', e => {
        if (!wmOpen) return;
        e.preventDefault();
        if (wmView === 'world') { if (e.deltaY < 0) drillHome(); return; }
        wmSetZoom(wmZoom + (e.deltaY < 0 ? 0.5 : -0.5));
      }, { passive: false });
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
      // graphics quality + reduced-motion popover (gear button by the 🔊)
      (function setupGfxMenu() {
        const btn = $('gfx-toggle'), menu = $('gfx-menu');
        if (!btn || !menu || !MH.gfx) return;
        const seg = $('gfx-seg'), sw = $('gfx-motion');
        const tseg = $('gfx-textsize'), soundSw = $('gfx-sound'), dmgSw = $('gfx-dmgnum'), contrastSw = $('gfx-contrast');
        const soundOn = () => lsGet('misthollow_ambience') !== 'off';
        const sync = () => {
          seg.querySelectorAll('span').forEach(s => s.classList.toggle('on', s.dataset.q === MH.gfx.quality));
          sw.classList.toggle('on', MH.gfx.reducedMotion);
          if (tseg) tseg.querySelectorAll('span').forEach(s => s.classList.toggle('on', s.dataset.t === MH.prefs.textSize));
          if (soundSw) soundSw.classList.toggle('on', soundOn());
          if (dmgSw) dmgSw.classList.toggle('on', MH.prefs.dmgNumbers);
          if (contrastSw) contrastSw.classList.toggle('on', MH.prefs.highContrast);
        };
        sync();
        btn.addEventListener('click', e => { e.stopPropagation(); menu.classList.toggle('show'); sync(); if (MH.sfx) MH.sfx.ui(); });
        seg.querySelectorAll('span').forEach(s => s.addEventListener('click', () => {
          MH.gfx.setQuality(s.dataset.q); sync(); flash('Graphics quality: ' + s.dataset.q); if (MH.sfx) MH.sfx.ui();
        }));
        sw.addEventListener('click', () => {
          MH.gfx.setReducedMotion(!MH.gfx.reducedMotion); sync();
          flash(MH.gfx.reducedMotion ? 'Reduced motion ON' : 'Reduced motion off'); if (MH.sfx) MH.sfx.ui();
        });
        // text size
        if (tseg) tseg.querySelectorAll('span').forEach(s => s.addEventListener('click', () => {
          MH.prefs.textSize = s.dataset.t; lsSet('mh_text_size', s.dataset.t); applyPrefs(); sync();
          flash('Text size: ' + s.dataset.t); if (MH.sfx) MH.sfx.ui();
        }));
        // sound (reuses the 🔊 ambience toggle so one switch governs all audio)
        if (soundSw) soundSw.addEventListener('click', () => {
          const amb = $('ambience-toggle'); if (amb) amb.click(); sync();
          flash(soundOn() ? 'Sound on' : 'Sound muted');
        });
        // floating damage numbers
        if (dmgSw) dmgSw.addEventListener('click', () => {
          MH.prefs.dmgNumbers = !MH.prefs.dmgNumbers; lsSet('mh_dmg_numbers', MH.prefs.dmgNumbers ? '1' : '0'); sync();
          flash(MH.prefs.dmgNumbers ? 'Damage numbers ON' : 'Damage numbers off'); if (MH.sfx) MH.sfx.ui();
        });
        // high contrast
        if (contrastSw) contrastSw.addEventListener('click', () => {
          MH.prefs.highContrast = !MH.prefs.highContrast; lsSet('mh_high_contrast', MH.prefs.highContrast ? '1' : '0'); applyPrefs(); sync();
          flash(MH.prefs.highContrast ? 'High contrast ON' : 'High contrast off'); if (MH.sfx) MH.sfx.ui();
        });
        const ctrlBtn = $('gfx-controls');
        if (ctrlBtn) ctrlBtn.addEventListener('click', () => { menu.classList.remove('show'); openControls(); });
        document.addEventListener('click', e => {
          if (menu.classList.contains('show') && !menu.contains(e.target) && e.target !== btn) menu.classList.remove('show');
        });
      })();
      // ---- controls / keybinds reference overlay (discoverability) ----
      const helpToggleBtn = $('help-toggle');
      if (helpToggleBtn) helpToggleBtn.addEventListener('click', () => openControls());
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
      // riding indicator: which mount you're on, click to dismount
      const mountChip = $('mount-chip');
      const updateMountChip = p => {
        if (!mountChip || !p) return;
        const m = p.mount;
        if (m) {
          const ic = mountIcon(m);
          const loy = (m.loyalty != null && m.loyalty < 50) ? ' · restless' : '';
          mountChip.textContent = `${ic} riding ${m.name}${loy}`;
          mountChip.style.display = 'block';
        } else mountChip.style.display = 'none';
      };
      if (mountChip) mountChip.addEventListener('click', () => { MH.sendCommand('dismount', false); setTimeout(MH.refreshState, 600); });
      MH.bus.on('map', payload => { updateHud(payload.player); renderMinimap(); updateVignette(); autofillBar(); updatePathChip(payload.player); updateMountChip(payload.player); renderContacts(payload); if (payload.player) MH.combat.syncServerCooldowns(payload.player.cooldowns); });
      MH.bus.on('target.set', () => renderContacts(MH.state.lastPayload));
      MH.bus.on('target.clear', () => renderContacts(MH.state.lastPayload));
      // quest tracker: refresh on room change (cheap) + throttle
      let qtLastVnum = null;
      MH.bus.on('map', payload => {
        const v = payload.player && payload.player.vnum;
        if (v !== qtLastVnum) { qtLastVnum = v; refreshQuestTracker(true); }
        else refreshQuestTracker(false);
      });
      MH.bus.on('login.success', () => setTimeout(() => refreshQuestTracker(true), 1500));
      MH.bus.on('login.success', () => setTimeout(loadAbilityCosts, 1800));
      MH.bus.on('map', () => updateHotbarAffordability());
      MH.bus.on('combat.update', () => updateHotbarAffordability());
      // resting chip + regen float, and live-refresh the recovery panel
      MH.bus.on('map', payload => { updateRestChip(payload.player); if (recoveryOpen) refreshRecovery(); });
      MH.bus.on('combat.update', payload => updateRestChip(payload.player));
      els.restChip.addEventListener('click', () => toggleRecovery(true));
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
      MH.bus.on('chat', e => { chatLine(e.line); clogLine(e.line.replace(/\x1b\[[0-9;]*m/g, '').replace(/</g, '&lt;'), 'chat'); });
      MH.bus.on('room.entered', ({ room }) => clogLine(`→ ${(room && room.name) || 'You move on'}`, 'info'));
      MH.bus.on('target.set', setTarget);
      // optimistic target HP: move the bar the instant a hit lands instead of
      // waiting for the next server poll, then let target.update reconcile it
      MH.bus.on('combat.hit', e => {
        if (!currentTarget || e.dmg == null) return;
        const a = MH.mobKeyword(currentTarget.name || ''), b = MH.mobKeyword(e.target || '');
        if (!a || !b || (a !== b && !a.includes(b) && !b.includes(a))) return;
        const max = currentTarget.maxHp || 1;
        const hp = Math.max(0, (currentTarget.hp != null ? currentTarget.hp : max) - e.dmg);
        currentTarget = Object.assign({}, currentTarget, { hp });
        setTarget(currentTarget);
      });
      // live combat log: every exchange visible at a glance
      // persistent, scrollable combat log keeping a long history; auto-scrolls
      // to the newest line unless you've scrolled up to read back
      const clogLine = (text, cls) => {
        clogLineRef = clogLine;
        const cl = els.combatLog, lines = els.combatLogLines;
        const nearBottom = cl.scrollHeight - cl.scrollTop - cl.clientHeight < 60;
        const div = document.createElement('div');
        div.className = cls;
        const t = new Date();
        div.innerHTML = `<span class="clog-t">${String(t.getHours()).padStart(2, '0')}:${String(t.getMinutes()).padStart(2, '0')}:${String(t.getSeconds()).padStart(2, '0')}</span> ${text}`;
        lines.appendChild(div);
        while (lines.children.length > 250) lines.removeChild(lines.firstChild);
        cl.classList.add('show');
        if (nearBottom) cl.scrollTop = cl.scrollHeight;
      };
      // compact action toast (eat/drink/equip) + mirror into the combat log
      const itemToast = (icon, label, name, logText) => {
        toast(`${icon} ${label}`, name || '', 'item');
        clogLine(logText || label, 'info');
      };
      // header tools: clear + collapse
      const clogClear = $('clog-clear'), clogCollapse = $('clog-collapse');
      if (clogClear) clogClear.addEventListener('click', e => { e.stopPropagation(); els.combatLogLines.innerHTML = ''; });
      if (clogCollapse) clogCollapse.addEventListener('click', e => {
        e.stopPropagation();
        const c = els.combatLog.classList.toggle('collapsed');
        clogCollapse.textContent = c ? '▸' : '▾';
      });
      MH.bus.on('combat.hit', e => clogLine(e.dmg != null ? `You hit ${e.target} for <b>${e.dmg}</b>` : `You hit ${e.target}`, 'you'));
      MH.bus.on('reaction.swing.perfect', () => clogLine('★ PERFECT STRIKE!', 'you'));
      MH.bus.on('mob.staggered', e => clogLine(`💥 ${e.name} is <b>STAGGERED</b> — strike now!`, 'info'));
      MH.bus.on('mob.guardup', e => {
        clogLine(`🛡 ${e.name} raises a guard — bash or kick to break it`, 'info');
        teach('guard', 'A 🛡 GUARD blunts your weapon swings — abilities pierce it, and a bash or kick SHATTERS it.');
      });
      MH.bus.on('mob.guardbreak', e => clogLine(`💥 ${e.name}'s guard is BROKEN`, 'you'));
      MH.bus.on('reaction.evade', () => clogLine('You dart clear of the danger zone!', 'you'));
      MH.bus.on('env.event', e => {
        const line = String(e.line);
        clogLine(line.replace(/</g, '&lt;'), 'info');
        // the environment has a voice: thuds, snaps, shatters, whooshes
        try {
          if (MH.fx && MH.fx.tone) {
            if (/BOOM/.test(line)) MH.fx.tone({ f: 90, f2: 42, type: 'sine', dur: 0.22, vol: 0.09 });
            else if (/💥 CRACK/.test(line)) MH.fx.tone({ f: 240, f2: 55, type: 'square', dur: 0.2, vol: 0.08 });
            else if (/SHUNK|snare (?:whips|snaps)|caltrops/.test(line)) MH.fx.tone({ f: 340, f2: 90, type: 'square', dur: 0.1, vol: 0.07 });
            else if (/noxious gas/.test(line)) MH.fx.tone({ f: 180, f2: 320, type: 'sawtooth', dur: 0.3, vol: 0.04 });
            else if (/❄💥|SHATTERS under/.test(line)) MH.fx.tone({ f: 1400, f2: 360, type: 'triangle', dur: 0.24, vol: 0.06 });
            else if (/BURNING|webs catch/.test(line)) MH.fx.tone({ f: 160, f2: 620, type: 'sawtooth', dur: 0.3, vol: 0.05 });
            else if (/frozen into a sheet|crackles and stills/.test(line)) MH.fx.tone({ f: 900, f2: 1500, type: 'sine', dur: 0.3, vol: 0.04 });
            else if (/pool LIGHTS UP/.test(line)) MH.fx.tone({ f: 1000, f2: 120, type: 'sawtooth', dur: 0.18, vol: 0.06 });
          }
        } catch (_) {}
      });
      MH.bus.on('combat.taken', e => clogLine(e && e.dmg != null ? `${e.from || 'They'} hit YOU for <b>${e.dmg}</b>` : 'They hit YOU', 'them'));
      MH.bus.on('combat.miss', e => clogLine(`You miss ${e.target}`, 'miss'));
      MH.bus.on('combat.dodged', () => clogLine('They miss you', 'miss'));
      MH.bus.on('defense.parry', e => clogLine(`You parry ${e.from || 'the attack'}`, 'def'));
      MH.bus.on('defense.dodge', () => clogLine('You dodge the attack', 'def'));
      MH.bus.on('defense.block', () => clogLine('You block the attack', 'def'));
      MH.bus.on('attack.parried', e => clogLine(`${e.target} parries your attack`, 'miss'));
      MH.bus.on('attack.dodged', e => clogLine(`${e.target} dodges`, 'miss'));
      MH.bus.on('attack.blocked', e => clogLine(`${e.target} blocks`, 'miss'));
      MH.bus.on('player.heal', () => clogLine('You are healed', 'heal'));
      MH.bus.on('level.up', () => clogLine('★ You gain a level!', 'info'));
      MH.bus.on('player.gold', e => clogLine(`+${e.amount} gold`, 'info'));
      MH.bus.on('item.loot', e => clogLine(e.from ? `◈ Looted <b>${e.item}</b> from ${e.from}` : `◈ Looted <b>${e.item}</b>`, 'loot'));
      MH.bus.on('mob.death', e => clogLine(`${e.name || 'It'} dies!`, 'info'));
      MH.bus.on('skill.improve', e => {
        const name = String(e.skill).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        toast(e.kind === 'spell' ? '✦ Spell Improved' : '▲ Skill Improved', `${name} — ${e.to}%`, 'skillup');
        clogLine(`▲ ${name} grows: ${e.from}% → <b>${e.to}%</b>`, 'heal');
        sparkleHotbarSkill(e.skill);
        if (MH.sfx && MH.sfx.ui) MH.sfx.ui();
      });
      MH.bus.on('skill.evolve', e => {
        cinematicEvolve(e.ability, e.evolution);
        clogLine(`✦ <b>${e.ability}</b> evolved → <b>${e.evolution}</b>`, 'info');
      });
      // consumables & gear: brief corner toast + combat-log line + sfx
      const titleCase = s => (s || '').replace(/^(a|an|the)\s+/i, '').replace(/\b\w/g, c => c.toUpperCase());
      MH.bus.on('item.consume', e => {
        if (e.kind === 'eat') {
          if (e.sated === false && !e.item) { itemToast('🍽', 'Still hungry', null, 'You eat but are still hungry'); return; }
          itemToast('🍖', 'You eat', e.item, `You eat ${e.item}`);
        } else {
          const what = e.liquid ? `${e.liquid}` : 'a drink';
          itemToast('🍷', 'You drink', e.liquid ? e.liquid : (e.item || ''), `You drink ${what}`);
        }
        if (MH.sfx && MH.sfx.ui) MH.sfx.ui();
      });
      MH.bus.on('item.equip', e => {
        const nm = titleCase(e.item);
        if (e.slot === 'light') { itemToast('🔆', 'Light source held', nm, `You hold ${e.item} aloft`); }
        else if (e.slot === 'wield') { itemToast('⚔', 'Weapon ready', nm, `You wield ${e.item}`); }
        else { itemToast('🛡', 'Equipped', nm, `You wear ${e.item}`); }
        if (MH.sfx && MH.sfx.ui) MH.sfx.ui();
      });
      MH.bus.on('item.unequip', e => { itemToast('🎒', 'Unequipped', titleCase(e.item), `You remove ${e.item}`); if (MH.sfx && MH.sfx.uiBack) MH.sfx.uiBack(); });
      MH.bus.on('player.exp', e => clogLine(`+${e.amount} experience`, 'info'));
      MH.bus.on('combat.flee', () => clogLine('You flee!', 'info'));
      MH.bus.on('combat.state', on => { duelShow(on); });

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

      // combat liveliness: the fighting box reacts to every blow so it never
      // feels static. A struck foe row flashes + shows the damage; taking a
      // hit flares your own portrait.
      const floatDmg = (host, text, color) => {
        if (!host) return;
        const n = document.createElement('div');
        n.className = 'duel-hit-num';
        n.textContent = text;
        n.style.color = color;
        n.style.left = '50%';
        n.style.top = '4px';
        n.style.transform = 'translateX(-50%)';
        if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
        host.appendChild(n);
        setTimeout(() => n.remove(), 900);
      };
      MH.bus.on('combat.hit', e => {
        const card = $('duel-card');
        if (!card || !card.classList.contains('show')) return;
        const rows = card.querySelectorAll('.foe-row');
        let row = card.querySelector('.foe-row.active') || rows[0];
        if (e && e.target) {
          const t = String(e.target).toLowerCase();
          rows.forEach(r => { const nm = r.querySelector('.fr-nm'); if (nm && nm.textContent.toLowerCase().includes(t)) row = r; });
        }
        if (row) {
          row.classList.remove('struck'); void row.offsetWidth; row.classList.add('struck');
          if (e && e.dmg != null) floatDmg(row, `-${e.dmg}`, '#ffd86a');
        }
      });
      MH.bus.on('combat.taken', e => {
        const card = $('duel-card');
        if (!card || !card.classList.contains('show')) return;
        const you = card.querySelector('.duel-side.you');
        if (you) { you.classList.remove('struck'); void you.offsetWidth; you.classList.add('struck');
          if (e && e.dmg != null) floatDmg(you, `-${e.dmg}`, '#ff7a7a'); }
      });

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

      // next-swing timer: synced to the server's real combat round (~4s). The
      // server pushes combat.update on every round boundary, so we restart the
      // fill on each push and size it to the true round length.
      const roundFill = els.roundBar && els.roundBar.querySelector('.fill');
      MH.bus.on('combat.update', payload => {
        MH.combat.noteRound();
        if (payload && payload.player) MH.combat.syncServerCooldowns(payload.player.cooldowns);
        teach('sweetspot', 'See the GOLD window on the round bar? Press F inside it to land a PERFECT strike.');
        if ((payload.mobs || []).some(m => m.poise && m.poise.cur > 0)) {
          teach('poise', 'The amber pips under an enemy are its BALANCE — fill them and it STAGGERS, wide open.');
        }
        els.roundBar.classList.add('show');
        els.roundBar.classList.remove('tick', 'perfect');
        void els.roundBar.offsetWidth;
        if (roundFill) roundFill.style.animationDuration = MH.combat.roundMs + 'ms';
        els.roundBar.classList.add('tick');
      });
      // a timed swing landed in the sweet spot: the bar turns gold until the
      // perfect strike resolves next round
      MH.bus.on('reaction.swing.ready', () => els.roundBar.classList.add('perfect'));
      MH.bus.on('combat.state', on => { if (!on) els.roundBar.classList.remove('show', 'tick'); });
      // continuously paint hotbar cooldown / round overlays from MH.combat
      setInterval(tickHotbarCooldowns, 100);

      // ---- declared enemy intent: wind-up bar + reaction prompt (Q/E/X) ----
      // A mob that telegraphs its next special arrives in the round payload as
      // mobs[i].intent {kind,label,interruptible,resolve_in}. Show WHAT is
      // coming, a red bar filling to when it lands, and the reactions that
      // actually counter it. Clicking a chip (or its hotkey) sends the command.
      const windup = $('enemy-windup'), rstrip = $('reaction-strip');
      const fireReaction = k => {
        const chip = rstrip && rstrip.querySelector(`.rchip[data-r="${k}"]`);
        if (!rstrip || !rstrip.classList.contains('show') || !chip) return false;
        if (chip.classList.contains('na') || chip.classList.contains('off')) return false;
        MH.sendCommand(k, false);
        chip.classList.add('off');   // optimistic; the next round push corrects it
        if (MH.sfx) MH.sfx.ui();
        return true;
      };
      window.fireReaction = fireReaction;   // used by the global hotkey handler
      if (rstrip) rstrip.querySelectorAll('.rchip').forEach(chip =>
        chip.addEventListener('click', () => fireReaction(chip.dataset.r)));
      const updateIntentUI = payload => {
        if (!windup || !rstrip) return;
        const mobs = (payload && payload.mobs) || [];
        const m = mobs.find(x => x.intent);
        if (!m) { windup.classList.remove('show'); rstrip.classList.remove('show'); return; }
        const it = m.intent;
        windup.querySelector('.nm').textContent = `⚠ ${String(m.name).toUpperCase()} — ${it.label}`;
        const fill = windup.querySelector('.fill');
        const total = 4.0, rem = Math.max(0.15, Math.min(total, it.resolve_in || total));
        // animate from the true elapsed fraction — never accumulate drift
        fill.style.transition = 'none';
        fill.style.width = ((1 - rem / total) * 100) + '%';
        void fill.offsetWidth;
        fill.style.transition = `width ${rem}s linear`;
        fill.style.width = '100%';
        windup.classList.add('show');
        const ready = (payload && payload.player && payload.player.reactions) || {};
        const applies = {
          brace: it.kind === 'heavy' || it.kind === 'aoe' || it.kind === 'debuff',
          sidestep: it.kind === 'heavy' || it.kind === 'aoe',
          interrupt: !!it.interruptible,
        };
        rstrip.querySelectorAll('.rchip').forEach(chip => {
          const k = chip.dataset.r;
          chip.classList.toggle('na', !applies[k]);
          chip.classList.toggle('off', ready[k] === false);
        });
        rstrip.classList.add('show');
        teach('windup', 'That red bar is an enemy WIND-UP — react with Q brace, E sidestep, or X interrupt (or just keep hitting).');
      };
      MH.bus.on('combat.update', updateIntentUI);
      MH.bus.on('combat.state', on => {
        if (!on && windup && rstrip) { windup.classList.remove('show'); rstrip.classList.remove('show'); }
      });

      // ---- environment UI: hazard chips + smart context strip ----
      // Hazard chips show WHAT the room holds (💧🔥🕸🌿🪨⚠❄); the context strip
      // shows only the actions that make sense right now, each with a hotkey:
      // stand by a door → door verbs; a detected trap → [U] disarm; thief or
      // ranger at peace → [O] lay a trap. Keys are context-gated: with no chip
      // showing, the same keys keep their normal panel meanings.
      let lastEnv = null;
      MH.bus.on('map', p => { if (p.current_room && p.current_room.env) lastEnv = p.current_room.env; });
      MH.bus.on('combat.update', p => { if (p.env) lastEnv = p.env; });
      // the packing column for all center chrome (see #center-stack CSS)
      const centerStack = document.createElement('div');
      centerStack.id = 'center-stack';
      document.body.appendChild(centerStack);
      window.__centerStack = centerStack;
      const hazEl = document.createElement('div');
      hazEl.id = 'room-hazards';
      centerStack.appendChild(hazEl);
      const envEl = document.createElement('div');
      envEl.id = 'env-strip';
      centerStack.appendChild(envEl);
      if (els.momentumChip) centerStack.appendChild(els.momentumChip);
      const spEl = document.getElementById('spender-menu');
      if (spEl) centerStack.appendChild(spEl);
      window.__envChips = null;
      const CASTERS = ['mage', 'necromancer', 'cleric', 'paladin'];
      const updateEnvUI = () => {
        const env = lastEnv;
        // hazard chips
        let hz = '';
        if (env) {
          if (env.burning) hz += `<span class="hz hot" title="the room is BURNING">🔥 BURNING</span>`;
          else if (env.fire) hz += `<span class="hz" title="open flames here">🔥</span>`;
          if (env.frozen) hz += `<span class="hz cold" title="the water is frozen — walkable ice">❄ FROZEN</span>`;
          else if (env.water) hz += `<span class="hz" title="water here">💧</span>`;
          if (env.webbed) hz += `<span class="hz" title="thick webs — highly flammable">🕸</span>`;
          if (env.brambles) hz += `<span class="hz" title="thorns rake everyone who fights here">🌿</span>`;
          if (env.ledge) hz += `<span class="hz" title="a drop — heavy blows can send someone over">🪨</span>`;
          if (env.trap && env.trap.detected) {
            hz += `<span class="hz warn" title="detected ${env.trap.kind} trap">${env.trap.deadly ? '☠' : '⚠'} TRAP</span>`;
            teach('trap', 'Trap spotted! Press U (or click the ⚠) to disarm it — or leave it armed and lure a foe onto it.');
          }
          if (env.ptraps) hz += `<span class="hz own" title="your traps are set here">🚧×${env.ptraps}</span>`;
        }
        if (hz) teach('hazards', 'Those chips under the room name are HAZARDS — water, fire, webs, thorns. Fights can use them.');
        hazEl.innerHTML = hz;
        hazEl.classList.toggle('show', !!hz);
        // context action chips
        const chips = [];
        const sc = MH.game && MH.game.scene.getScenes(true).find(s => s.getNearbyDoor);
        const door = sc ? sc.getNearbyDoor() : null;
        const cls = String((MH.state.player && MH.state.player.char_class) || '').toLowerCase();
        if (door) {
          const d = door.dir;
          if (door.state === 'closed') {
            chips.push(['G', door.locked ? 'Locked door' : 'Open', door.locked ? null : `open ${d}`]);
            chips.push(['B', 'Bash', `bash ${d}`]);
            chips.push(['V', 'Barricade', `barricade ${d}`]);
            chips.push(['L', door.locked ? 'Unlock' : 'Lock', door.locked ? `unlock ${d}` : `lock ${d}`]);
            if (CASTERS.includes(cls)) chips.push(['P', 'Seal', `seal ${d}`]);
          } else if (!door.broken) {
            chips.push(['G', 'Close', `close ${d}`]);
          }
        }
        if (env && env.trap && env.trap.detected) chips.push(['U', 'Disarm trap', 'disarm trap']);
        if (!MH.state.inCombat && (cls === 'thief' || cls === 'ranger')) {
          chips.push(['O', cls === 'thief' ? 'Caltrops' : 'Snare', cls === 'thief' ? 'caltrops' : 'snare']);
        }
        if (!chips.length) {
          envEl.classList.remove('show');
          window.__envChips = null;
          return;
        }
        const sig = JSON.stringify(chips);
        if (envEl.dataset.sig !== sig) {
          envEl.dataset.sig = sig;
          envEl.innerHTML = chips.map(([k, label, cmd]) =>
            `<span class="ec ${cmd ? '' : 'dim'}" data-cmd="${cmd || ''}"><b>${k}</b> ${label}</span>`).join('');
          envEl.querySelectorAll('.ec[data-cmd]').forEach(elc =>
            elc.addEventListener('click', () => { if (elc.dataset.cmd) MH.sendCommand(elc.dataset.cmd, false); }));
        }
        envEl.classList.add('show');
        window.__envChips = {};
        chips.forEach(([k, label, cmd]) => { if (cmd) window.__envChips[k.toLowerCase()] = cmd; });
      };
      setInterval(updateEnvUI, 400);

      // timed door work (barricading, sealing, lockpicking) shows on the cast
      // bar; any movement key abandons it (cancel instantly, never stuck)
      window.__envChannel = false;
      MH.bus.on('env.channel', e => {
        window.__envChannel = true;
        els.castBar.querySelector('.nm').textContent = `${e.label}…`;
        els.castBar.style.setProperty('--cast-ms', (e.secs * 1000) + 'ms');
        els.castBar.classList.remove('go', 'done');
        void els.castBar.offsetWidth;
        els.castBar.classList.add('show', 'go');
        setTimeout(() => { window.__envChannel = false; els.castBar.classList.remove('show', 'go', 'done'); }, e.secs * 1000 + 400);
      });
      MH.bus.on('env.channel.end', () => {
        window.__envChannel = false;
        els.castBar.classList.remove('show', 'go', 'done');
      });

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

      // permanent stance selector, built into the HUD beside the vitals so the
      // player can always see and change their combat stance (not just in a fight)
      const STANCES = [
        { id: 'aggressive', icon: '⚔', label: 'AGGRO', tip: 'Aggressive — +hit, +damage, but easier to hit' },
        { id: 'normal', icon: '⚖', label: 'NORMAL', tip: 'Normal — balanced offense and defense' },
        { id: 'defensive', icon: '🛡', label: 'DEFEND', tip: 'Defensive — better block & dodge, less offense' },
      ];
      const hudStances = $('hud-stances');
      if (hudStances) {
        STANCES.forEach(s => {
          const div = document.createElement('div');
          div.className = 'hud-stance';
          div.dataset.st = s.id;
          div.title = s.tip;
          if (s.id === 'normal') div.classList.add('active');   // default until state confirms
          div.innerHTML = `<span class="si">${s.icon}</span><span>${s.label}</span>`;
          div.addEventListener('click', () => {
            commandWithPeek(`stance ${s.id}`);
            setStance(s.id);                       // optimistic; state refresh confirms
            if (MH.state.player) MH.state.player.stance = s.id;
            if (MH.sfx) MH.sfx.ui();
          });
          hudStances.appendChild(div);
        });
      }
      const setStance = st => {
        const cur = String(st || '').toLowerCase();
        if (hudStances) hudStances.querySelectorAll('.hud-stance').forEach(d =>
          d.classList.toggle('active', d.dataset.st === cur));
        // keep the legacy floating bar (if present) in sync but it stays hidden
        if (els.stanceBar) els.stanceBar.querySelectorAll('.stance').forEach(d =>
          d.classList.toggle('active', d.dataset.st === cur));
      };
      MH.bus.on('combat.state', on => {
        if (!on) {
          els.momentumChip.classList.remove('show');
          els.finisherChip.classList.remove('show');
          const sp = document.getElementById('spender-menu');
          if (sp) sp.classList.remove('show');
        }
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
      // ---- build → spend: the class resource SPENDER menu ----
      // The decision layer for every class loop: while you're fighting, your
      // signature resource's spenders appear under the resource chip — lit
      // when affordable, dim when not. Click one to spend. (Server validates
      // costs; this only surfaces the choice that already exists.)
      const CLASS_SPENDERS = {
        thief:       [['Pocket Sand', 'pocket sand', 3], ['Low Blow', 'low blow', 5], ['Rigged Dice', 'rigged dice', 7], ['Jackpot', 'jackpot', 10]],
        assassin:    [['Expose', 'expose', 3], ['Vital Strike', 'vital', 6], ['Execute Contract', 'execute contract', 10]],
        necromancer: [['Soul Bolt', 'soul bolt', 2], ['Drain Soul', 'drain soul', 3], ['Bone Shield', 'bone shield', 4], ['Soul Reap', 'soul reap', 8]],
        paladin:     [['Word of Glory', 'word of glory', 3]],
        cleric:      [['Divine Word', 'divine word', 3], ['Holy Fire', 'holy fire', 5], ['Divine Intervention', 'divine intervention', 10]],
        ranger:      [['Kill Command', 'kill command', 25], ['Aimed Shot', 'aimed shot', 30], ['Rapid Fire', 'rapid fire', 50]],
        bard:        [['Encore', 'encore', 2], ['Discordant Note', 'discordant note', 4], ['Crescendo', 'crescendo', 5], ['Magnum Opus', 'magnum opus', 10]],
      };
      let spenderEl = null, spenderSig = '';
      const renderSpenderMenu = p => {
        if (!spenderEl) {
          spenderEl = document.createElement('div');
          spenderEl.id = 'spender-menu';
          (window.__centerStack || document.body).appendChild(spenderEl);
        }
        const cls = String(p.char_class || '').toLowerCase();
        const r = p.resource;
        const list = CLASS_SPENDERS[cls];
        // warrior's climax is automatic — tease it as Momentum nears full
        if (cls === 'warrior' && MH.state.inCombat && r && r.value >= 7 && r.value < r.max) {
          const sig = `w${r.value}`;
          if (spenderSig !== sig) {
            spenderSig = sig;
            spenderEl.innerHTML = `<div class="sp-row dim">🔥 ${r.max}× Momentum = UNSTOPPABLE</div>`;
          }
          spenderEl.classList.add('show');
          return;
        }
        const cheapest = list && list.length ? list[0][2] : Infinity;
        if (!MH.state.inCombat || !r || !list || !list.length || r.value < cheapest) {
          spenderEl.classList.remove('show');
          spenderSig = '';
          return;
        }
        const sig = cls + '|' + list.map(s => r.value >= s[2] ? 1 : 0).join('');
        if (spenderSig !== sig) {
          spenderSig = sig;
          spenderEl.innerHTML = list.map(([label, cmd, cost]) =>
            `<div class="sp-row ${r.value >= cost ? '' : 'dim'}" data-cmd="${cmd}" title="spend ${cost} ${r.name}">${label} <b>${cost}</b></div>`
          ).join('');
          spenderEl.querySelectorAll('.sp-row[data-cmd]').forEach(row =>
            row.addEventListener('click', () => { MH.sendCommand(row.dataset.cmd, false); if (MH.sfx) MH.sfx.ui(); }));
        }
        spenderEl.classList.add('show');
      };
      // one-time, per-character primer on the class's signature resource — the
      // combat system was reinvented around these, so teach them on first use
      const RES_HINT = {
        warrior: '🔥 Momentum builds as you land blows — spend it on finishers like Execute.',
        cleric: '🕯 Faith builds as you smite and heal — spend it on miracles like Serenity.',
        paladin: '✨ Holy Power builds from Dawnstrikes — spend it on Verdict of the Order or Absolution.',
        necromancer: '💀 Soul Shards are harvested from the dying — spend them on Wraithfire and Reap.',
        ranger: '🎯 Focus regenerates over time — spend it on Truesight Shot and Loosing Storm.',
        thief: '🍀 Luck builds from dirty tricks — gamble it on The Big Score (jackpot).',
        assassin: '🗡 Intel builds as you Mark a target — cash it in for a guaranteed kill.',
        bard: '🎵 Inspiration builds as you perform — spend it on a Crescendo.',
        mage: '✦ Arcane Charges build from Towerbolt — release them with Resonance Burst.',
      };
      function maybeResourceHint(p) {
        if (!p || !p.char_class) return;
        const cls = String(p.char_class).toLowerCase();
        const key = `mh_reshint_${(p.name || '').toLowerCase()}_${cls}`;
        if (lsGet(key) === '1' || !RES_HINT[cls]) return;
        lsSet(key, '1');
        setTimeout(() => flash(RES_HINT[cls]), 1200);
      }
      MH.bus.on('combat.update', payload => { if (payload.player) maybeResourceHint(payload.player); });
      MH.bus.on('map', payload => { if (payload.player) { renderResourceChip(payload.player); renderSpenderMenu(payload.player); } });
      MH.bus.on('combat.update', payload => {
        MH.state.lastCombatMobs = payload.mobs;
        const p = payload.player || {};
        renderResourceChip(p);
        renderSpenderMenu(p);
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
      MH.bus.on('level.up', () => cinematicLevelUp());
      MH.bus.on('shop.open', openShop);
      MH.bus.on('training.open', openTraining);
      MH.bus.on('npc.talk', openDialogue);

      // command input
      els.commandInput.addEventListener('focus', () => setTyping(true));
      els.commandInput.addEventListener('blur', () => setTyping(false));
      // catch-all: ANY editable element (login, creation, chat, command, future)
      // pauses world input + key capture so letters like WASD reach the field
      const isEditable = el => !!el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
      document.addEventListener('focusin', e => { if (isEditable(e.target)) setTyping(true); });
      document.addEventListener('focusout', e => { if (isEditable(e.target)) setTyping(false); });
      els.commandInput.addEventListener('keydown', e => {
        e.stopPropagation();
        if (e.key === 'Enter') {
          const cmd = els.commandInput.value.trim();
          if (cmd) { runTypedCommand(cmd); els.commandInput.value = ''; }
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
        if (e.key === '?') { e.preventDefault(); openControls(); return; }
        // pressing a panel's own hotkey again closes it (toggle)
        {
          const tk = e.key.toLowerCase();
          const KEY_MODAL = { i: 'modal-inv', j: 'modal-journal', k: 'modal-spells', n: 'modal-spells',
            y: 'modal-almanac', b: 'modal-services', c: 'modal-stable', l: 'modal-legend', v: 'modal-travel' };
          const mid = KEY_MODAL[tk];
          if (mid) { const el = document.getElementById(mid); if (el && el.classList.contains('open')) { closeModals(); return; } }
        }
        if (anyModalOpen()) return;
        // Shift+WASD = compass move, Shift+Q/E = up/down
        if (e.shiftKey) {
          const navKey = { w: 'north', a: 'west', s: 'south', d: 'east', q: 'up', e: 'down' }[e.key.toLowerCase()];
          if (navKey) { e.preventDefault(); MH.bus.emit('nav.goto', navKey); return; }
        }
        if (e.key >= '0' && e.key <= '9') { useHotbar(e.key === '0' ? 9 : Number(e.key) - 1); return; }
        // combat reactions to a declared enemy wind-up (only when the prompt
        // is showing and the chip is usable — otherwise the key falls through)
        if (!e.shiftKey && ['q', 'e', 'x'].includes(e.key.toLowerCase()) && window.fireReaction) {
          const rk = { q: 'brace', e: 'sidestep', x: 'interrupt' }[e.key.toLowerCase()];
          if (window.fireReaction(rk)) { e.preventDefault(); return; }
        }
        // environment context chips (door verbs, disarm, lay trap): the key
        // acts only while its chip is visible, otherwise panels keep it
        if (!e.shiftKey && window.__envChips && window.__envChips[e.key.toLowerCase()]) {
          MH.sendCommand(window.__envChips[e.key.toLowerCase()], false);
          e.preventDefault();
          return;
        }
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
        else if (k === 'v') { openTravel(); }
        else if (k === 'z') { toggleRecovery(); }
        if (['a', 'd', 'w', 's', 'arrowleft', 'arrowright', 'arrowup', 'arrowdown', ' '].includes(k)) {
          cancelWalk();
          // moving abandons any timed door work — you're never stuck
          if (window.__envChannel) { MH.sendCommand('stopwork', false); MH.bus.emit('env.channel.end'); }
          // moving dismisses the room prose so it never blocks the view
          els.roomDesc.classList.remove('show');
        }
        if (e.key === ' ') e.preventDefault(); // don't scroll the page
      });
    },
  };
})();
